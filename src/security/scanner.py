"""
Security Scanner - Snyk & SonarQube integration
Automated vulnerability scanning
"""

import os
import subprocess
import json
from typing import Dict, Optional
from pathlib import Path


class SecurityScanner:
    """Centralized security scanning with Snyk and SonarQube"""
    
    def __init__(self):
        self.snyk_token = os.getenv("SNYK_TOKEN", "")
        self.sonar_token = os.getenv("SONAR_TOKEN", "")
        self.sonar_host = os.getenv("SONAR_HOST_URL", "http://localhost:9000")
        self.project_root = Path(__file__).parent.parent.parent
    
    def scan_snyk_code(self, target_path: Optional[str] = None) -> Dict:
        """
        Run Snyk Code scan for code vulnerabilities
        
        Args:
            target_path: Path to scan (default: project root)
        
        Returns:
            Dict with scan results
        """
        if not self.snyk_token:
            return {
                "status": "skipped",
                "message": "SNYK_TOKEN not configured"
            }
        
        scan_path = target_path or str(self.project_root)
        
        try:
            # Set Snyk token
            env = os.environ.copy()
            env["SNYK_TOKEN"] = self.snyk_token
            
            # Run Snyk code test
            result = subprocess.run(
                ["snyk", "code", "test", scan_path, "--json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=300
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                return {
                    "status": "completed",
                    "scan_type": "snyk_code",
                    "vulnerabilities": self._parse_snyk_results(data),
                    "raw_output": data
                }
            
            return {
                "status": "failed",
                "message": result.stderr or "Snyk scan failed"
            }
        
        except subprocess.TimeoutExpired:
            return {"status": "failed", "message": "Scan timeout"}
        except FileNotFoundError:
            return {"status": "failed", "message": "Snyk CLI not installed"}
        except Exception as e:
            return {"status": "failed", "message": str(e)}
    
    def scan_snyk_dependencies(self, target_path: Optional[str] = None) -> Dict:
        """
        Run Snyk dependency scan
        
        Args:
            target_path: Path to scan
        
        Returns:
            Dict with scan results
        """
        if not self.snyk_token:
            return {
                "status": "skipped",
                "message": "SNYK_TOKEN not configured"
            }
        
        scan_path = target_path or str(self.project_root)
        
        try:
            env = os.environ.copy()
            env["SNYK_TOKEN"] = self.snyk_token
            
            result = subprocess.run(
                ["snyk", "test", scan_path, "--json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=300
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                return {
                    "status": "completed",
                    "scan_type": "snyk_dependencies",
                    "vulnerabilities": self._parse_snyk_results(data),
                    "raw_output": data
                }
            
            return {
                "status": "failed",
                "message": result.stderr or "Dependency scan failed"
            }
        
        except Exception as e:
            return {"status": "failed", "message": str(e)}
    
    def scan_sonarqube(self, project_key: str = "moustass-video") -> Dict:
        """
        Trigger SonarQube scan
        
        Args:
            project_key: SonarQube project key
        
        Returns:
            Dict with scan status
        """
        if not self.sonar_token:
            return {
                "status": "skipped",
                "message": "SONAR_TOKEN not configured"
            }
        
        try:
            # Run sonar-scanner
            result = subprocess.run(
                [
                    "sonar-scanner",
                    f"-Dsonar.projectKey={project_key}",
                    f"-Dsonar.host.url={self.sonar_host}",
                    f"-Dsonar.login={self.sonar_token}",
                    f"-Dsonar.projectBaseDir={self.project_root}"
                ],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                return {
                    "status": "completed",
                    "scan_type": "sonarqube",
                    "message": "SonarQube scan completed",
                    "dashboard_url": f"{self.sonar_host}/dashboard?id={project_key}"
                }
            
            return {
                "status": "failed",
                "message": result.stderr or "SonarQube scan failed"
            }
        
        except FileNotFoundError:
            return {"status": "failed", "message": "sonar-scanner not installed"}
        except Exception as e:
            return {"status": "failed", "message": str(e)}
    
    def _parse_snyk_results(self, data: Dict) -> Dict:
        """Parse Snyk JSON output to extract severity counts"""
        vulnerabilities = data.get("vulnerabilities", [])
        
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            "total": len(vulnerabilities),
            "by_severity": severity_counts,
            "issues": vulnerabilities[:10]  # First 10 for preview
        }
    
    def get_scan_summary(self) -> Dict:
        """
        Run all scans and return comprehensive summary
        
        Returns:
            Dict with all scan results
        """
        return {
            "snyk_code": self.scan_snyk_code(),
            "snyk_dependencies": self.scan_snyk_dependencies(),
            "sonarqube": self.scan_sonarqube()
        }
