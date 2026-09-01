document.addEventListener('DOMContentLoaded', () => {
  let productsData = [];
  let currentFilter = 'all';
  let chartInstance = null;

  // DOM Elements
  const productsGrid = document.getElementById('productsGrid');
  const emptyState = document.getElementById('emptyState');
  const addForm = document.getElementById('addForm');
  const btnAddSubmit = document.getElementById('btnAddSubmit');
  const addBtnSpinner = document.getElementById('addBtnSpinner');
  const addBtnText = document.getElementById('addBtnText');
  
  const statTotal = document.getElementById('statTotal');
  const statDrops = document.getElementById('statDrops');
  const statAmazon = document.getElementById('statAmazon');
  const statFlipkart = document.getElementById('statFlipkart');

  const btnCheckAll = document.getElementById('btnCheckAll');
  const btnOpenSettings = document.getElementById('btnOpenSettings');
  const settingsModal = document.getElementById('settingsModal');
  const btnCloseSettings = document.getElementById('btnCloseSettings');
  const settingsForm = document.getElementById('settingsForm');
  const btnTestTelegram = document.getElementById('btnTestTelegram');

  const historyModal = document.getElementById('historyModal');
  const btnCloseHistory = document.getElementById('btnCloseHistory');
  const historyModalTitle = document.getElementById('historyModalTitle');

  // Filter Buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentFilter = e.target.dataset.filter;
      renderProducts();
    });
  });

  // Fetch and Render Products
  async function fetchProducts() {
    try {
      const res = await fetch('/api/products');
      const data = await res.json();
      if (data.success) {
        productsData = data.products;
        updateStats();
        renderProducts();
      }
    } catch (err) {
      showToast('Failed to load products', 'error');
    }
  }

  function updateStats() {
    statTotal.textContent = productsData.length;
    
    const drops = productsData.filter(p => p.current_price && p.current_price <= p.target_price).length;
    statDrops.textContent = drops;
    
    const amazonCount = productsData.filter(p => p.platform === 'Amazon').length;
    statAmazon.textContent = amazonCount;
    
    const flipkartCount = productsData.filter(p => p.platform === 'Flipkart').length;
    statFlipkart.textContent = flipkartCount;
  }

  function renderProducts() {
    productsGrid.innerHTML = '';
    
    let filtered = productsData;
    if (currentFilter === 'drop') {
      filtered = productsData.filter(p => p.current_price && p.current_price <= p.target_price);
    } else if (currentFilter !== 'all') {
      filtered = productsData.filter(p => p.platform === currentFilter);
    }

    if (filtered.length === 0) {
      emptyState.classList.remove('hidden');
      return;
    } else {
      emptyState.classList.add('hidden');
    }

    filtered.forEach(product => {
      const isDrop = product.current_price && product.current_price <= product.target_price;
      const formattedCurrent = product.current_price ? `₹${product.current_price.toLocaleString('en-IN')}` : 'Unavailable';
      const formattedTarget = `₹${product.target_price.toLocaleString('en-IN')}`;

      const card = document.createElement('div');
      card.className = 'product-card';
      card.innerHTML = `
        <span class="platform-badge badge-${product.platform.toLowerCase()}">${product.platform}</span>
        
        <div class="product-info">
          <img src="${product.image_url}" alt="Product Image" class="product-img" onerror="this.src='https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=300'">
          <div class="product-details">
            <h4>${product.title}</h4>
            <span class="subtext">Checked: ${formatDate(product.last_checked)}</span>
          </div>
        </div>

        <div class="price-row">
          <div>
            <div class="current-price ${isDrop ? 'price-drop' : ''}">${formattedCurrent}</div>
            <div class="target-price">
              Target: ${formattedTarget}
              <button class="btn-edit-target" data-id="${product.id}" data-target="${product.target_price}" title="Edit Target Price">✏️</button>
            </div>
          </div>
          ${isDrop ? '<span class="status-drop">🔥 PRICE DROP!</span>' : ''}
        </div>

        <div class="card-actions">
          <a href="${product.url}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">🔗 Store</a>
          <div class="action-buttons">
            <button class="btn btn-secondary btn-sm btn-history" data-id="${product.id}">📈 History</button>
            <button class="btn btn-secondary btn-sm btn-check" data-id="${product.id}">🔄 Re-check</button>
            <button class="btn btn-danger btn-sm btn-delete" data-id="${product.id}">🗑️</button>
          </div>
        </div>
      `;

      productsGrid.appendChild(card);
    });

    // Attach Action Event Listeners
    document.querySelectorAll('.btn-check').forEach(btn => {
      btn.addEventListener('click', (e) => checkSingleProduct(e.target.dataset.id, e.target));
    });

    document.querySelectorAll('.btn-delete').forEach(btn => {
      btn.addEventListener('click', (e) => openDeleteModal(e.target.dataset.id));
    });

    document.querySelectorAll('.btn-history').forEach(btn => {
      btn.addEventListener('click', (e) => openHistoryChart(e.target.dataset.id));
    });

    document.querySelectorAll('.btn-edit-target').forEach(btn => {
      btn.addEventListener('click', (e) => openEditTargetModal(e.target.dataset.id, e.target.dataset.target));
    });
  }

  // State for Modals
  let activeEditProductId = null;
  let activeDeleteProductId = null;

  // Edit Target Modal Elements
  const editTargetModal = document.getElementById('editTargetModal');
  const editTargetForm = document.getElementById('editTargetForm');
  const editTargetProductTitle = document.getElementById('editTargetProductTitle');
  const inputNewTarget = document.getElementById('inputNewTarget');
  const btnCloseEditTarget = document.getElementById('btnCloseEditTarget');
  const btnCancelEditTarget = document.getElementById('btnCancelEditTarget');

  // Confirm Delete Modal Elements
  const confirmDeleteModal = document.getElementById('confirmDeleteModal');
  const deleteProductPreview = document.getElementById('deleteProductPreview');
  const btnCloseDeleteModal = document.getElementById('btnCloseDeleteModal');
  const btnCancelDelete = document.getElementById('btnCancelDelete');
  const btnConfirmDelete = document.getElementById('btnConfirmDelete');

  // Open Edit Target Modal
  function openEditTargetModal(id, currentTarget) {
    activeEditProductId = id;
    const prod = productsData.find(p => p.id == id);
    editTargetProductTitle.textContent = prod ? prod.title : 'Product';
    inputNewTarget.value = currentTarget;
    editTargetModal.classList.add('active');
  }

  function closeEditTargetModal() {
    editTargetModal.classList.remove('active');
    activeEditProductId = null;
  }

  btnCloseEditTarget.addEventListener('click', closeEditTargetModal);
  btnCancelEditTarget.addEventListener('click', closeEditTargetModal);

  editTargetForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!activeEditProductId) return;

    const newTarget = parseFloat(inputNewTarget.value);
    if (isNaN(newTarget) || newTarget <= 0) {
      showToast('Please enter a valid price greater than 0', 'error');
      return;
    }

    try {
      const res = await fetch(`/api/products/${activeEditProductId}/target`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_price: newTarget })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Target price updated!', 'success');
        closeEditTargetModal();
        fetchProducts();
      } else {
        showToast(data.error || 'Failed to update target price', 'error');
      }
    } catch (err) {
      showToast('Error updating target price', 'error');
    }
  });

  // Open Confirm Delete Modal
  function openDeleteModal(id) {
    activeDeleteProductId = id;
    const prod = productsData.find(p => p.id == id);
    deleteProductPreview.textContent = prod ? prod.title : 'Selected Product';
    confirmDeleteModal.classList.add('active');
  }

  function closeDeleteModal() {
    confirmDeleteModal.classList.remove('active');
    activeDeleteProductId = null;
  }

  btnCloseDeleteModal.addEventListener('click', closeDeleteModal);
  btnCancelDelete.addEventListener('click', closeDeleteModal);

  btnConfirmDelete.addEventListener('click', async () => {
    if (!activeDeleteProductId) return;
    try {
      const res = await fetch(`/api/products/${activeDeleteProductId}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        showToast('Product removed', 'success');
        closeDeleteModal();
        fetchProducts();
      }
    } catch (err) {
      showToast('Failed to delete product', 'error');
    }
  });

  // Re-check All Products
  btnCheckAll.addEventListener('click', async () => {
    btnCheckAll.disabled = true;
    btnCheckAll.textContent = '⏳ Re-checking All...';
    try {
      const res = await fetch('/api/products/check-all', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast('All items checked!', 'success');
        fetchProducts();
      }
    } catch (err) {
      showToast('Error running check-all', 'error');
    } finally {
      btnCheckAll.disabled = false;
      btnCheckAll.innerHTML = '<span class="icon">🔄</span> Re-check All';
    }
  });

  // History Chart Modal
  async function openHistoryChart(prodId) {
    const prod = productsData.find(p => p.id == prodId);
    if (!prod) return;
    
    historyModalTitle.textContent = `Price History: ${prod.title.slice(0, 30)}...`;
    historyModal.classList.add('active');

    try {
      const res = await fetch(`/api/products/${prodId}/history`);
      const data = await res.json();
      
      if (data.success && data.history) {
        renderChart(data.history, prod.target_price);
      }
    } catch (err) {
      showToast('Failed to load history chart', 'error');
    }
  }

  function renderChart(historyPoints, targetPrice) {
    const ctx = document.getElementById('historyChart').getContext('2d');
    
    if (chartInstance) {
      chartInstance.destroy();
    }

    const labels = historyPoints.map(p => formatDate(p.timestamp));
    const prices = historyPoints.map(p => p.price);

    chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Tracked Price (₹)',
            data: prices,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            fill: true,
            tension: 0.3
          },
          {
            label: 'Target Threshold (₹)',
            data: new Array(historyPoints.length).fill(targetPrice),
            borderColor: '#ef4444',
            borderDash: [5, 5],
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: '#f8fafc' } }
        },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  }

  btnCloseHistory.addEventListener('click', () => historyModal.classList.remove('active'));

  // Settings Modal Handlers
  btnOpenSettings.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/settings');
      const data = await res.json();
      if (data.success) {
        document.getElementById('cfgTelegramToken').value = data.settings.telegram_bot_token || '';
        document.getElementById('cfgTelegramChatId').value = data.settings.telegram_chat_id || '';
        document.getElementById('cfgInterval').value = data.settings.check_interval_hours || '4';
      }
    } catch (err) {}
    settingsModal.classList.add('active');
  });

  btnCloseSettings.addEventListener('click', () => settingsModal.classList.remove('active'));

  settingsForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const telegram_bot_token = document.getElementById('cfgTelegramToken').value.trim();
    const telegram_chat_id = document.getElementById('cfgTelegramChatId').value.trim();
    const check_interval_hours = document.getElementById('cfgInterval').value;

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ telegram_bot_token, telegram_chat_id, check_interval_hours })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Settings saved successfully!', 'success');
        settingsModal.classList.remove('active');
      }
    } catch (err) {
      showToast('Error saving settings', 'error');
    }
  });

  btnTestTelegram.addEventListener('click', async () => {
    const telegram_bot_token = document.getElementById('cfgTelegramToken').value.trim();
    const telegram_chat_id = document.getElementById('cfgTelegramChatId').value.trim();

    if (!telegram_bot_token || !telegram_chat_id) {
      showToast('Please fill in both Bot Token and Chat ID first', 'error');
      return;
    }

    btnTestTelegram.disabled = true;
    btnTestTelegram.textContent = '⏳ Sending Alert...';
    try {
      const res = await fetch('/api/test-notification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ telegram_bot_token, telegram_chat_id })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Check your Telegram app! Test message sent.', 'success');
      } else {
        showToast(data.message || data.error || 'Failed to send test alert', 'error');
      }
    } catch (err) {
      showToast('Error sending test notification', 'error');
    } finally {
      btnTestTelegram.disabled = false;
      btnTestTelegram.textContent = '⚡ Test Notification';
    }
  });

  // Utilities
  function formatDate(ts) {
    if (!ts) return 'Never';
    const date = new Date(ts);
    return date.toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function showToast(msg, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span> ${msg}`;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  // Initial Load
  fetchProducts();
});
