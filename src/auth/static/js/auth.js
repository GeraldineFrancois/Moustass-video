function validatePassword(pwd){
  if(pwd.length < 8) return false;
  if(!/[A-Z]/.test(pwd)) return false;
  if(!/[a-z]/.test(pwd)) return false;
  if(!/[^A-Za-z0-9]/.test(pwd)) return false;
  return true;
}

document.addEventListener('DOMContentLoaded', ()=>{
  const f = document.getElementById('signupForm');
  if(f){
    f.addEventListener('submit', (e)=>{
      const pwd = f.password.value;
      const confirm = f.confirm_password.value;
      if(!validatePassword(pwd)){
        e.preventDefault();
        alert('Mot de passe doit contenir 8 caractères, maj, min et caractère spécial');
        return;
      }
      if(pwd !== confirm){
        e.preventDefault();
        alert('Les mots de passe ne correspondent pas');
      }
    });
  }
});
