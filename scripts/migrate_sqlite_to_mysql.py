#!/usr/bin/env python3
"""
migrate_sqlite_to_mysql.py

Copy selected tables from a local SQLite dev.db to a MySQL DATABASE_URL.

Usage:
  python scripts/migrate_sqlite_to_mysql.py --dest <mysql-url> [--source <sqlite-url>] [--execute]

By default the script runs in dry-run mode and only reports what would be done.
Set --execute to perform the inserts.
"""
from __future__ import annotations
import os
import argparse
import logging
from typing import Dict

from sqlalchemy import create_engine, MetaData, Table, select, and_
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def connect(url: str) -> Engine:
    logger.info("Connecting to %s", url)
    engine = create_engine(url)
    # quick connect test
    with engine.connect() as conn:
        conn.execute(select(1))
    return engine


def reflect_table(engine: Engine, table_name: str) -> Table | None:
    md = MetaData()
    try:
        md.reflect(bind=engine, only=[table_name])
    except Exception:
        return None
    return md.tables.get(table_name)


def row_to_dict(row) -> Dict:
    # SQLAlchemy Row can be turned into dict via _mapping in modern versions
    try:
        return dict(row._mapping)
    except Exception:
        return dict(row)


def migrate_users(src_engine: Engine, dst_engine: Engine, users_table: Table, execute: bool) -> Dict[int, int]:
    """Migrate users. Returns mapping source_id -> dest_id."""
    mapping: Dict[int, int] = {}
    src_conn = src_engine.connect()
    sel = select(users_table)
    rows = src_conn.execute(sel).fetchall()
    # Use an explicit transaction for destination inserts so they are committed
    # before we proceed to dependent tables (users_logs, signatures).
    if execute:
        dst_ctx = dst_engine.begin()
        dst_conn = dst_ctx.__enter__()
    else:
        dst_conn = dst_engine.connect()
    inserted = 0
    skipped = 0
    for r in rows:
        data = row_to_dict(r)
        src_id = data.get('id')
        email = data.get('email')
        # check existing by email
        existing = dst_conn.execute(select(users_table).where(users_table.c.email == email)).fetchone()
        if existing:
            existing_data = row_to_dict(existing)
            mapping[src_id] = int(existing_data['id'])
            skipped += 1
            continue
        logger.info("Will insert user %s (id=%s)", email, src_id)
        if execute:
            # Do not force primary key 'id' on insert; let MySQL assign it.
            insert_data = {k: v for k, v in data.items() if k != 'id'}
            ins = users_table.insert().values(**insert_data)
            res = dst_conn.execute(ins)
            # try to get inserted primary key
            try:
                new_id = int(res.inserted_primary_key[0])
            except Exception:
                # fallback: query by email
                new = dst_conn.execute(select(users_table).where(users_table.c.email == email)).fetchone()
                new_id = int(row_to_dict(new)['id'])
            mapping[src_id] = new_id
            inserted += 1
        else:
            # dry run: pretend we preserved id
            mapping[src_id] = src_id
            inserted += 1

    src_conn.close()
    if execute:
        # commit happens when exiting the context manager
        dst_ctx.__exit__(None, None, None)
    else:
        dst_conn.close()
    logger.info("Users: inserted=%d skipped=%d", inserted, skipped)
    return mapping


def migrate_code_files(src_engine: Engine, dst_engine: Engine, table_name: str, mapping_users: Dict[int, int], execute: bool) -> Dict[int, int]:
    md_src = MetaData(); md_src.reflect(bind=src_engine, only=[table_name])
    md_dst = MetaData(); md_dst.reflect(bind=dst_engine, only=[table_name])
    src_tbl = md_src.tables.get(table_name)
    dst_tbl = md_dst.tables.get(table_name)
    if src_tbl is None or dst_tbl is None:
        logger.info("Table %s not present on one side, skipping.", table_name)
        return {}
    src_conn = src_engine.connect()
    rows = src_conn.execute(select(src_tbl)).fetchall()
    if execute:
        dst_ctx = dst_engine.begin()
        dst_conn = dst_ctx.__enter__()
    else:
        dst_conn = dst_engine.connect()
    mapping_files: Dict[int, int] = {}
    inserted = 0; skipped = 0
    for r in rows:
        data = row_to_dict(r)
        src_id = data.get('id')
        # remap user id if available
        uid = data.get('user_id')
        if uid in mapping_users:
            data['user_id'] = mapping_users[uid]
        # avoid duplicates by file_hash + user_id
        exists = dst_conn.execute(select(dst_tbl).where(and_(dst_tbl.c.file_hash == data.get('file_hash'), dst_tbl.c.user_id == data.get('user_id')))).fetchone()
        if exists:
            mapping_files[src_id] = int(row_to_dict(exists)['id'])
            skipped += 1
            continue
        logger.info("Will insert code_file id=%s name=%s", src_id, data.get('file_name'))
        if execute:
            res = dst_conn.execute(dst_tbl.insert().values(**data))
            try:
                new_id = int(res.inserted_primary_key[0])
            except Exception:
                new = dst_conn.execute(select(dst_tbl).where(dst_tbl.c.file_hash == data.get('file_hash'))).fetchone()
                new_id = int(row_to_dict(new)['id'])
            mapping_files[src_id] = new_id
            inserted += 1
        else:
            mapping_files[src_id] = src_id
            inserted += 1

    src_conn.close()
    if execute:
        dst_ctx.__exit__(None, None, None)
    else:
        dst_conn.close()
    logger.info("Code files: inserted=%d skipped=%d", inserted, skipped)
    return mapping_files


def migrate_signatures(src_engine: Engine, dst_engine: Engine, table_name: str, mapping_files: Dict[int, int], mapping_users: Dict[int, int], execute: bool):
    md_src = MetaData(); md_src.reflect(bind=src_engine, only=[table_name])
    md_dst = MetaData(); md_dst.reflect(bind=dst_engine, only=[table_name])
    src_tbl = md_src.tables.get(table_name)
    dst_tbl = md_dst.tables.get(table_name)
    if src_tbl is None or dst_tbl is None:
        logger.info("Table %s not present on one side, skipping.", table_name)
        return
    src_conn = src_engine.connect()
    rows = src_conn.execute(select(src_tbl)).fetchall()
    if execute:
        dst_ctx = dst_engine.begin()
        dst_conn = dst_ctx.__enter__()
    else:
        dst_conn = dst_engine.connect()
    inserted = 0; skipped = 0
    for r in rows:
        data = row_to_dict(r)
        if data.get('file_id') in mapping_files:
            data['file_id'] = mapping_files[data['file_id']]
        if data.get('user_id') in mapping_users:
            data['user_id'] = mapping_users[data['user_id']]
        # avoid duplicates by signature_value + file_id + user_id
        exists = dst_conn.execute(select(dst_tbl).where(and_(dst_tbl.c.signature_value == data.get('signature_value'), dst_tbl.c.file_id == data.get('file_id'), dst_tbl.c.user_id == data.get('user_id')))).fetchone()
        if exists:
            skipped += 1
            continue
        logger.info("Will insert signature for file_id=%s user_id=%s", data.get('file_id'), data.get('user_id'))
        if execute:
            dst_conn.execute(dst_tbl.insert().values(**data))
            inserted += 1
        else:
            inserted += 1

    src_conn.close()
    if execute:
        dst_ctx.__exit__(None, None, None)
    else:
        dst_conn.close()
    logger.info("Signatures: inserted=%d skipped=%d", inserted, skipped)


def migrate_users_logs(src_engine: Engine, dst_engine: Engine, table_name: str, mapping_users: Dict[int, int], execute: bool):
    md_src = MetaData(); md_src.reflect(bind=src_engine, only=[table_name])
    md_dst = MetaData(); md_dst.reflect(bind=dst_engine, only=[table_name])
    src_tbl = md_src.tables.get(table_name)
    dst_tbl = md_dst.tables.get(table_name)
    if src_tbl is None or dst_tbl is None:
        logger.info("Table %s not present on one side, skipping.", table_name)
        return
    src_conn = src_engine.connect()
    rows = src_conn.execute(select(src_tbl)).fetchall()
    if execute:
        dst_ctx = dst_engine.begin()
        dst_conn = dst_ctx.__enter__()
    else:
        dst_conn = dst_engine.connect()
    inserted = 0; skipped = 0
    for r in rows:
        data = row_to_dict(r)
        if data.get('user_id') in mapping_users:
            data['user_id'] = mapping_users[data['user_id']]
        # avoid duplicates by action_type + log_date + user_id
        exists = dst_conn.execute(select(dst_tbl).where(and_(dst_tbl.c.action_type == data.get('action_type'), dst_tbl.c.log_date == data.get('log_date'), dst_tbl.c.user_id == data.get('user_id')))).fetchone()
        if exists:
            skipped += 1
            continue
        logger.info("Will insert users_log action=%s user_id=%s", data.get('action_type'), data.get('user_id'))
        if execute:
            dst_conn.execute(dst_tbl.insert().values(**data))
            inserted += 1
        else:
            inserted += 1

    src_conn.close()
    if execute:
        dst_ctx.__exit__(None, None, None)
    else:
        dst_conn.close()
    logger.info("Users logs: inserted=%d skipped=%d", inserted, skipped)


def main():
    parser = argparse.ArgumentParser(description='Migrate selected tables from SQLite to MySQL')
    parser.add_argument('--source', default=os.environ.get('SOURCE_SQLITE', 'sqlite:///./dev.db'), help='Source DB URL (default: sqlite:///./dev.db)')
    parser.add_argument('--dest', default=os.environ.get('DATABASE_URL'), help='Destination DB URL (MySQL) or set DATABASE_URL env var')
    parser.add_argument('--execute', action='store_true', help='Actually perform inserts. Without this flag the script runs in dry-run mode.')
    args = parser.parse_args()

    if not args.dest:
        logger.error('Destination URL not provided. Set --dest or DATABASE_URL env var.')
        return

    logger.info('Source: %s', args.source)
    logger.info('Dest:   %s', args.dest)
    logger.info('Mode: %s', 'EXECUTE' if args.execute else 'DRY-RUN')

    src_engine = connect(args.source)
    dst_engine = connect(args.dest)

    # reflect necessary tables and migrate in sensible order
    users_tbl = reflect_table(src_engine, 'users')
    if users_tbl is None:
        logger.error('No users table found in source, aborting.')
        return

    # Migrate users first and build id mapping
    mapping_users = migrate_users(src_engine, dst_engine, users_tbl, execute=args.execute)

    # Migrate code_files
    mapping_files = migrate_code_files(src_engine, dst_engine, 'code_files', mapping_users, execute=args.execute)

    # Migrate signatures
    migrate_signatures(src_engine, dst_engine, 'signatures', mapping_files, mapping_users, execute=args.execute)

    # Migrate users_logs
    migrate_users_logs(src_engine, dst_engine, 'users_logs', mapping_users, execute=args.execute)

    logger.info('Migration dry-run complete. Rerun with --execute to perform the inserts.' if not args.execute else 'Migration complete.')


if __name__ == '__main__':
    main()
