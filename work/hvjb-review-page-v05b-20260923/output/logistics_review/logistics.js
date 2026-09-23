"use strict";
const choices = [...document.querySelectorAll("[data-pick]")];
const panels = [...document.querySelectorAll("[data-step]")];
for (const button of choices) {
  button.addEventListener("click", () => {
    const key = button.dataset.pick;
    for (const panel of panels) panel.hidden = panel.dataset.step !== key;
    for (const choice of choices) choice.setAttribute("aria-pressed", String(choice === button));
  });
}
