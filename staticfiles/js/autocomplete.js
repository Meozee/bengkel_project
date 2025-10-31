document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".item-autocomplete").forEach((input) => {
    setupAutocomplete(input);
  });

  function setupAutocomplete(input) {
    const suggestionBox = document.createElement("div");
    suggestionBox.classList.add("autocomplete-box");
    input.parentNode.appendChild(suggestionBox);

    input.addEventListener("input", async function () {
      const query = this.value.trim();
      if (query.length < 2) {
        suggestionBox.innerHTML = "";
        return;
      }

      try {
        const response = await fetch(`/inventory/autocomplete/?q=${encodeURIComponent(query)}`);
        const results = await response.json();

        suggestionBox.innerHTML = "";
        results.forEach((item) => {
          const option = document.createElement("div");
          option.classList.add("autocomplete-item");
          option.textContent = `${item.name} - Rp ${item.price.toLocaleString("id-ID")}`;
          option.dataset.id = item.id;
          option.dataset.price = item.price;

          option.addEventListener("click", () => {
            input.value = item.name;

            // Isi hidden input item.id
            const hiddenInput = input.parentNode.querySelector('input[type="hidden"]');
            hiddenInput.value = item.id;

            // Isi harga satuan otomatis
            const row = input.closest(".item-row");
            const priceInput = row.querySelector('[name$="unit_price"]');
            priceInput.value = item.price;

            suggestionBox.innerHTML = "";
          });

          suggestionBox.appendChild(option);
        });
      } catch (err) {
        console.error("Error fetching autocomplete data:", err);
      }
    });

    // Tutup dropdown kalau klik di luar
    document.addEventListener("click", (e) => {
      if (!suggestionBox.contains(e.target) && e.target !== input) {
        suggestionBox.innerHTML = "";
      }
    });
  }
});
