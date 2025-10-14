document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.item-autocomplete').forEach(input => {
    const hiddenInput = input.previousElementSibling; // form.item.as_hidden
    const listBox = document.createElement('div');
    listBox.classList.add('autocomplete-list');
    listBox.style.position = 'absolute';
    listBox.style.background = 'white';
    listBox.style.border = '1px solid #ccc';
    listBox.style.zIndex = '1000';
    listBox.style.width = input.offsetWidth + 'px';
    listBox.style.display = 'none';
    input.parentNode.style.position = 'relative';
    input.parentNode.appendChild(listBox);

    input.addEventListener('input', async () => {
      const query = input.value.trim();
      if (query.length < 2) {
        listBox.style.display = 'none';
        return;
      }
      const res = await fetch(`/transactions/item-autocomplete/?q=${query}`);
      const data = await res.json();

      listBox.innerHTML = '';
      data.forEach(item => {
        const option = document.createElement('div');
        option.textContent = `${item.name} — Rp ${item.price}`;
        option.style.padding = '4px 8px';
        option.style.cursor = 'pointer';
        option.addEventListener('click', () => {
          input.value = item.name;
          hiddenInput.value = item.id; // 🧠 ID dikirim ke backend
          const row = input.closest('tr');
          const priceField = row.querySelector('input[name$="unit_price"]');
          if (priceField) priceField.value = item.price;
          listBox.style.display = 'none';
        });
        listBox.appendChild(option);
      });
      listBox.style.display = data.length ? 'block' : 'none';
    });

    document.addEventListener('click', e => {
      if (!input.contains(e.target)) listBox.style.display = 'none';
    });
  });
});
