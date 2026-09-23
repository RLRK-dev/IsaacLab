"use strict";
const movie = document.querySelector("video");
const status = document.querySelector("#movie-position");
for (const button of document.querySelectorAll("button[data-seek]")) {
  button.addEventListener("click", () => {
    const seconds = Number(button.dataset.seek);
    movie.pause();
    movie.currentTime = seconds;
    status.textContent = `${button.dataset.scene} の開始位置へ移動しました。再生ボタンで確認できます。`;
    movie.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}
