let usernameChecked = false;

function checkUsername() {
    const username = document.getElementById('username').value;
    fetch('/check_username', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `username=${username}`
    })
    .then(response => response.json())
    .then(data => {
        const messageElement = document.getElementById('username-message');
        if (data.exists) {
            messageElement.textContent = '이미 존재하는 ID입니다.';
            messageElement.style.color = 'red';
            usernameChecked = false;
        } else {
            messageElement.textContent = '사용 가능한 ID입니다.';
            messageElement.style.color = 'green';
            usernameChecked = true;
        }
    });
}

function validateForm() {
    if (!usernameChecked) {
        alert('ID 중복 체크!');
        return false;
    }
    const emailCode = document.getElementById('email-code').value;
    if (!emailCode) {
        alert('인증 코드를 입력하세요!');
        return false;
    }
    return true;
}

function checkEmail() {
    const email = document.getElementById("email").value;
    fetch('/submit_email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `email=${email}`
    })
    .then(response => response.json())
    .then(data => {
        const messageElement = document.getElementById("email-message");
        if (data.success) {
            /*messageElement.textContent = '이메일이 성공적으로 전달되었습니다.';
            messageElement.style.color = 'green';*/
            document.getElementById('code-input-group').style.display = 'block';
        } else {
            messageElement.textContent = '이메일 전달에 실패했습니다.';
            messageElement.style.color = 'red';
        }
    })
    .catch(error => console.error('Error:', error));
}
