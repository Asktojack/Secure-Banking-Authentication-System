function validateLogin(){

    let username=document.getElementById("username").value.trim();

    let password=document.getElementById("password").value.trim();

    if(username===""){

        alert("Enter Username");

        return false;

    }

    if(password===""){

        alert("Enter Password");

        return false;

    }

    return true;

}