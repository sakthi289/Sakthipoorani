const ui = document.getElementById("ui");
const totalItems = 100;

for (let i = 1; i <= totalItems; i++) {
  const love = document.createElement("div");
  love.className = "love";
  love.style.setProperty("--i", i);

  love.innerHTML = `
    <div class="love_horizontal">
      <div class="love_vertical">
        <div class="love_word">SAKTHI</div>
      </div>
    </div>
  `;

  ui.appendChild(love);
}