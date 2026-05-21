const inventory = [
  { title: "Fruit Line A", detail: "12,000 u/h | Europe" },
  { title: "Fruit Line B", detail: "8,500 u/h | Spain" },
  { title: "Fruit Line C", detail: "15,000 u/h | Germany" },
  { title: "Flexo Folder Gluer", detail: "3-color | 2020" }
];

const grid = document.getElementById("inventory-grid");
inventory.forEach((item) => {
  const card = document.createElement("article");
  card.className = "card";
  card.innerHTML = `<h3>${item.title}</h3><p>${item.detail}</p>`;
  grid.appendChild(card);
});

const form = document.querySelector(".lead-form");
form?.addEventListener("submit", (e) => {
  e.preventDefault();
  alert("Thanks. Your valuation request was captured.");
});
