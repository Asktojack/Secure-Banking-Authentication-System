function validateRegister(){

    let fullname=document.getElementById("fullname").value.trim();

    let username=document.getElementById("username").value.trim();

    let email=document.getElementById("email").value.trim();

    let mobile=document.getElementById("mobile").value.trim();

    let password=document.getElementById("password").value.trim();

    if(fullname===""){

        alert("Enter Full Name");

        return false;

    }

    if(username===""){

        alert("Enter Username");

        return false;

    }

    if(email===""){

        alert("Enter Email");

        return false;

    }

    if(mobile===""){

        alert("Enter Mobile Number");

        return false;

    }

    if(password.length<8){

        alert("Password should contain at least 8 characters");

        return false;

    }

    return true;

}