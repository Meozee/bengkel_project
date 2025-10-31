document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  if (!form) return;

  // =================================================================
  // HELPER FUNCTIONS
  // =================================================================

  const formatCurrency = (value) => new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value);

  const parseCurrency = (value) => parseFloat(String(value).replace(/[^0-9,-]+/g, '').replace(',', '.')) || 0;

  // =================================================================
  // CALCULATION LOGIC
  // =================================================================

  function calculateRowSubtotal(row) {
    if (!row) return 0;

    const qty = parseFloat(row.querySelector('input[name$="-quantity"]')?.value) || 0;
    const price = parseFloat(row.querySelector('input[name$="-unit_price"]')?.value) || 0;
    const discount = parseFloat(row.querySelector('input[name$="-discount_percentage"]')?.value) || 0;
    const subtotalField = row.querySelector('.subtotal-field');

    const subtotal = (qty * price) * (1 - (discount / 100));

    if (subtotalField) {
      subtotalField.value = formatCurrency(subtotal);
    }
    return subtotal;
  }

  function updateGrandTotal() {
    let grandTotal = 0;
    document.querySelectorAll('#item-formset-body tr, #service-formset-body tr').forEach(row => {
      grandTotal += calculateRowSubtotal(row);
    });

    const otherCharges = parseFloat(form.querySelector('input[name="other_charges"]')?.value) || 0;
    const discountAmount = parseFloat(form.querySelector('input[name="discount_amount"]')?.value) || 0;

    grandTotal += otherCharges;
    grandTotal -= discountAmount;

    document.getElementById('grand-total').value = formatCurrency(grandTotal);
  }

  // =================================================================
  // DYNAMIC FORMSET LOGIC (ADD/REMOVE ROWS)
  // =================================================================

  function addFormRow(prefix, templateId, containerId) {
    const template = document.getElementById(templateId)?.innerHTML;
    if (!template) {
      console.error(`Template with ID #${templateId} not found.`);
      return;
    }

    const container = document.getElementById(containerId);
    const totalFormsInput = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    const formIndex = parseInt(totalFormsInput.value);

    const newRowHtml = template.replace(/__prefix__/g, formIndex);
    const newRow = document.createElement('tr');
    newRow.innerHTML = newRowHtml;
    // Beri class yang benar agar kalkulasi & penghapusan berfungsi
    newRow.className = `${prefix.slice(0, -1)}-form-row`; 
    
    container.appendChild(newRow);
    totalFormsInput.value = formIndex + 1;

    // Inisialisasi autocomplete jika ini adalah baris item
    if (prefix === 'items') {
      const autocompleteInput = newRow.querySelector('.item-autocomplete');
      if (autocompleteInput) {
        setupAutocomplete(autocompleteInput);
      }
    }
  }

  // =================================================================
  // AUTOCOMPLETE LOGIC
  // =================================================================

  function setupAutocomplete(input) {
    const row = input.closest('tr');
    const hiddenInput = row.querySelector('input[name$="-item"]'); // Target hidden input for item ID
    const listBox = document.createElement('div');
    listBox.className = 'autocomplete-list list-group position-absolute w-100';
    listBox.style.zIndex = '1050';
    input.parentNode.style.position = 'relative';
    input.parentNode.appendChild(listBox);

    let fetchTimeout;
    input.addEventListener('input', () => {
      clearTimeout(fetchTimeout);
      const query = input.value.trim();

      if (query.length < 2) {
        listBox.style.display = 'none';
        return;
      }

      fetchTimeout = setTimeout(async () => {
        try {
          const res = await fetch(`/transactions/item-autocomplete/?q=${encodeURIComponent(query)}`);
          const data = await res.json();
          
          listBox.innerHTML = '';
          data.forEach(item => {
            const option = document.createElement('a');
            option.href = '#';
            option.className = 'list-group-item list-group-item-action';
            option.textContent = `${item.name} — ${formatCurrency(item.price)}`;
            option.addEventListener('click', (e) => {
              e.preventDefault();
              input.value = item.name;
              hiddenInput.value = item.id;
              
              const priceField = row.querySelector('input[name$="unit_price"]');
              if (priceField) priceField.value = item.price;

              listBox.style.display = 'none';
              updateGrandTotal();
            });
            listBox.appendChild(option);
          });
          listBox.style.display = data.length ? 'block' : 'none';
        } catch (error) {
          console.error('Autocomplete Error:', error);
        }
      }, 250); // Debounce to avoid excessive requests
    });

    document.addEventListener('click', (e) => {
      if (!input.parentNode.contains(e.target)) {
        listBox.style.display = 'none';
      }
    });
  }


  // =================================================================
  // EVENT LISTENERS (USING DELEGATION)
  // =================================================================

  form.addEventListener('click', (e) => {
    // Tombol 'Tambah Item'
    if (e.target.id === 'add-item-btn') {
      addFormRow('items', 'item-form-template', 'item-formset-body');
    }
    // Tombol 'Tambah Service'
    if (e.target.id === 'add-service-btn') {
      addFormRow('services', 'service-form-template', 'service-formset-body');
    }
    // Tombol 'Hapus' baris
    if (e.target.classList.contains('remove-form-row')) {
      e.target.closest('tr').remove();
      updateGrandTotal();
    }
  });

  form.addEventListener('input', (e) => {
    const target = e.target;
    // Trigger kalkulasi jika ada input di field yang relevan
    if (target.matches('input[name$="-quantity"], input[name$="-unit_price"], input[name$="-discount_percentage"], input[name="other_charges"], input[name="discount_amount"]')) {
      updateGrandTotal();
    }
  });
  
  // =================================================================
  // INITIALIZATION
  // =================================================================
  
  // Inisialisasi autocomplete untuk baris yang sudah ada
  document.querySelectorAll('.item-autocomplete').forEach(setupAutocomplete);
  
  // Kalkulasi total awal saat halaman dimuat
  updateGrandTotal();
});