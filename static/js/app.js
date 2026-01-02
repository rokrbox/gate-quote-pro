// Gate Quote Pro - JavaScript

// State
let currentQuoteId = null;
let quoteItems = [];
let customers = [];
let materials = [];
let settings = {};

// ============== Initialization ==============

document.addEventListener('DOMContentLoaded', () => {
    loadCustomers();
    loadSettings();
    loadCategories();
});

// ============== Navigation ==============

function showPage(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    // Remove active from nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // Show selected page
    document.getElementById(page + 'Page').classList.add('active');

    // Set active nav
    document.querySelectorAll(`[data-page="${page}"], [onclick*="${page}"]`).forEach(n => n.classList.add('active'));

    // Close mobile menu
    document.getElementById('mobileMenu')?.classList.remove('open');

    // Load page data
    if (page === 'quotes') loadQuotes();
    if (page === 'customers') loadAllCustomers();
    if (page === 'priceList') loadMaterials();
    if (page === 'settings') loadSettings();
    if (page === 'newQuote') resetQuoteForm();
}

function toggleMenu() {
    document.getElementById('mobileMenu').classList.toggle('open');
}

// ============== Customers ==============

async function loadCustomers() {
    const response = await fetch('/api/customers');
    customers = await response.json();
    updateCustomerSelect();
}

function updateCustomerSelect() {
    const select = document.getElementById('customerSelect');
    select.innerHTML = '<option value="">-- Select Customer --</option>';
    customers.forEach(c => {
        select.innerHTML += `<option value="${c.id}">${c.name}</option>`;
    });
}

function onCustomerSelect() {
    const id = document.getElementById('customerSelect').value;
    const customer = customers.find(c => c.id == id);

    if (customer) {
        let info = '';
        if (customer.address) info += customer.address + '<br>';
        if (customer.city || customer.state) info += `${customer.city}, ${customer.state} ${customer.zip_code}<br>`;
        if (customer.phone) info += `Phone: ${customer.phone}<br>`;
        if (customer.email) info += `Email: ${customer.email}`;
        document.getElementById('customerInfo').innerHTML = info;
    } else {
        document.getElementById('customerInfo').innerHTML = '';
    }
}

async function loadAllCustomers() {
    const search = document.getElementById('customerSearch')?.value || '';
    const response = await fetch(`/api/customers?search=${encodeURIComponent(search)}`);
    const data = await response.json();
    renderCustomersList(data);
}

function searchCustomers() {
    loadAllCustomers();
}

function renderCustomersList(customerList) {
    const container = document.getElementById('customersList');
    if (customerList.length === 0) {
        container.innerHTML = '<p class="empty-message">No customers found</p>';
        return;
    }

    container.innerHTML = customerList.map(c => `
        <div class="customer-row">
            <div class="customer-info-card">
                <div class="customer-name">${c.name}</div>
                <div class="customer-contact">
                    ${c.phone || ''} ${c.phone && c.email ? '|' : ''} ${c.email || ''}
                </div>
            </div>
            <div class="row-actions">
                <button class="btn btn-small btn-secondary" onclick="editCustomer(${c.id})">Edit</button>
                <button class="btn btn-small btn-success" onclick="newQuoteForCustomer(${c.id})">New Quote</button>
                <button class="btn btn-small btn-danger" onclick="deleteCustomer(${c.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function showCustomerModal(customerId = null) {
    document.getElementById('editCustomerId').value = customerId || '';
    document.getElementById('customerModalTitle').textContent = customerId ? 'Edit Customer' : 'New Customer';

    if (customerId) {
        const c = customers.find(x => x.id == customerId);
        if (c) {
            document.getElementById('customerName').value = c.name;
            document.getElementById('customerEmail').value = c.email;
            document.getElementById('customerPhone').value = c.phone;
            document.getElementById('customerAddress').value = c.address;
            document.getElementById('customerCity').value = c.city;
            document.getElementById('customerState').value = c.state;
            document.getElementById('customerZip').value = c.zip_code;
            document.getElementById('customerNotes').value = c.notes;
        }
    } else {
        document.getElementById('customerName').value = '';
        document.getElementById('customerEmail').value = '';
        document.getElementById('customerPhone').value = '';
        document.getElementById('customerAddress').value = '';
        document.getElementById('customerCity').value = '';
        document.getElementById('customerState').value = '';
        document.getElementById('customerZip').value = '';
        document.getElementById('customerNotes').value = '';
    }

    openModal('customerModal');
}

function editCustomer(id) {
    showCustomerModal(id);
}

async function saveCustomer() {
    const id = document.getElementById('editCustomerId').value;
    const data = {
        name: document.getElementById('customerName').value,
        email: document.getElementById('customerEmail').value,
        phone: document.getElementById('customerPhone').value,
        address: document.getElementById('customerAddress').value,
        city: document.getElementById('customerCity').value,
        state: document.getElementById('customerState').value,
        zip_code: document.getElementById('customerZip').value,
        notes: document.getElementById('customerNotes').value
    };

    if (!data.name) {
        showToast('Name is required', 'error');
        return;
    }

    const url = id ? `/api/customers/${id}` : '/api/customers';
    const method = id ? 'PUT' : 'POST';

    await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    closeModal('customerModal');
    await loadCustomers();
    loadAllCustomers();
    showToast('Customer saved');
}

async function deleteCustomer(id) {
    if (!confirm('Delete this customer?')) return;

    await fetch(`/api/customers/${id}`, { method: 'DELETE' });
    await loadCustomers();
    loadAllCustomers();
    showToast('Customer deleted');
}

function newQuoteForCustomer(id) {
    document.getElementById('customerSelect').value = id;
    onCustomerSelect();
    showPage('newQuote');
}

// ============== Quotes ==============

async function loadQuotes() {
    const status = document.getElementById('statusFilter')?.value || '';
    const url = status ? `/api/quotes?status=${status}` : '/api/quotes';
    const response = await fetch(url);
    const data = await response.json();
    renderQuotesList(data);
}

function renderQuotesList(quotes) {
    const container = document.getElementById('quotesList');
    if (quotes.length === 0) {
        container.innerHTML = '<p class="empty-message">No quotes found</p>';
        return;
    }

    container.innerHTML = quotes.map(q => `
        <div class="quote-row">
            <div class="quote-info">
                <div class="quote-number">${q.quote_number}</div>
                <div class="quote-details">
                    ${q.customer_name} | ${formatValue(q.gate_type)} ${q.width}ft x ${q.height}ft | $${q.total.toFixed(2)}
                </div>
            </div>
            <span class="quote-status status-${q.status}">${q.status}</span>
            <div class="row-actions">
                <button class="btn btn-small btn-secondary" onclick="editQuote(${q.id})">Edit</button>
                <button class="btn btn-small btn-success" onclick="downloadPDF(${q.id})">PDF</button>
                <button class="btn btn-small btn-danger" onclick="deleteQuote(${q.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function editQuote(id) {
    const response = await fetch(`/api/quotes/${id}`);
    const quote = await response.json();

    currentQuoteId = quote.id;
    document.getElementById('customerSelect').value = quote.customer_id || '';
    onCustomerSelect();

    document.getElementById('gateType').value = quote.gate_type;
    document.getElementById('gateStyle').value = quote.gate_style;
    document.getElementById('width').value = quote.width;
    document.getElementById('height').value = quote.height;
    document.getElementById('material').value = quote.material;
    document.getElementById('automation').value = quote.automation;
    document.getElementById('accessControl').value = quote.access_control;
    document.getElementById('groundType').value = quote.ground_type;
    document.getElementById('slope').value = quote.slope;
    document.getElementById('powerDistance').value = quote.power_distance;
    document.getElementById('removalNeeded').checked = quote.removal_needed;
    document.getElementById('laborHours').value = quote.labor_hours;
    document.getElementById('laborRate').value = quote.labor_rate;
    document.getElementById('notes').value = quote.notes;

    quoteItems = quote.items || [];
    renderItems();
    updateSummary();

    document.getElementById('pdfBtn').style.display = 'inline-flex';
    showPage('newQuote');
}

async function deleteQuote(id) {
    if (!confirm('Delete this quote?')) return;

    await fetch(`/api/quotes/${id}`, { method: 'DELETE' });
    loadQuotes();
    showToast('Quote deleted');
}

async function downloadPDF(id) {
    window.open(`/api/quotes/${id}/pdf`, '_blank');
}

function resetQuoteForm() {
    currentQuoteId = null;
    document.getElementById('customerSelect').value = '';
    document.getElementById('customerInfo').innerHTML = '';
    document.getElementById('gateType').value = 'swing';
    document.getElementById('gateStyle').value = 'standard';
    document.getElementById('width').value = '12';
    document.getElementById('height').value = '6';
    document.getElementById('material').value = 'steel';
    document.getElementById('automation').value = 'none';
    document.getElementById('accessControl').value = 'none';
    document.getElementById('groundType').value = 'concrete';
    document.getElementById('slope').value = 'flat';
    document.getElementById('powerDistance').value = '0';
    document.getElementById('removalNeeded').checked = false;
    document.getElementById('laborHours').value = '0';
    document.getElementById('laborRate').value = settings.labor_rate || '125';
    document.getElementById('notes').value = '';

    quoteItems = [];
    renderItems();
    updateSummary();

    document.getElementById('pdfBtn').style.display = 'none';
}

// ============== Quote Calculation ==============

async function calculateQuote() {
    const data = getQuoteFormData();
    const response = await fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    const result = await response.json();

    document.getElementById('laborHours').value = result.labor_hours;
    document.getElementById('laborRate').value = result.labor_rate;

    quoteItems = result.items;
    renderItems();
    updateSummary();

    showToast('Quote calculated');
}

async function suggestMaterials() {
    await calculateQuote();
}

async function saveQuote() {
    const data = getQuoteFormData();
    data.items = quoteItems;
    data.labor_hours = parseFloat(document.getElementById('laborHours').value) || 0;
    data.labor_rate = parseFloat(document.getElementById('laborRate').value) || 125;

    const url = currentQuoteId ? `/api/quotes/${currentQuoteId}` : '/api/quotes';
    const method = currentQuoteId ? 'PUT' : 'POST';

    const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    const result = await response.json();

    if (!currentQuoteId && result.id) {
        currentQuoteId = result.id;
        document.getElementById('pdfBtn').style.display = 'inline-flex';
    }

    showToast('Quote saved');
}

async function generatePDF() {
    if (!currentQuoteId) {
        await saveQuote();
    }
    if (currentQuoteId) {
        downloadPDF(currentQuoteId);
    }
}

function getQuoteFormData() {
    return {
        customer_id: document.getElementById('customerSelect').value || null,
        gate_type: document.getElementById('gateType').value,
        gate_style: document.getElementById('gateStyle').value,
        width: parseFloat(document.getElementById('width').value) || 12,
        height: parseFloat(document.getElementById('height').value) || 6,
        material: document.getElementById('material').value,
        automation: document.getElementById('automation').value,
        access_control: document.getElementById('accessControl').value,
        ground_type: document.getElementById('groundType').value,
        slope: document.getElementById('slope').value,
        power_distance: parseFloat(document.getElementById('powerDistance').value) || 0,
        removal_needed: document.getElementById('removalNeeded').checked,
        notes: document.getElementById('notes').value
    };
}

// ============== Quote Items ==============

function renderItems() {
    const container = document.getElementById('itemsList');

    if (quoteItems.length === 0) {
        container.innerHTML = '<p class="empty-message">No items added. Click \'Auto-Suggest\' or \'Add Item\'.</p>';
        return;
    }

    container.innerHTML = quoteItems.map((item, idx) => `
        <div class="item-row">
            <span class="item-desc">${item.description}</span>
            <span class="item-qty">${item.quantity}</span>
            <span class="item-unit">${item.unit}</span>
            <span class="item-cost">$${item.unit_cost.toFixed(2)}</span>
            <span class="item-total">$${item.total_cost.toFixed(2)}</span>
            <button class="btn btn-small btn-danger" onclick="removeItem(${idx})">X</button>
        </div>
    `).join('');
}

function removeItem(idx) {
    quoteItems.splice(idx, 1);
    renderItems();
    updateSummary();
}

function updateSummary() {
    const materialsTotal = quoteItems.reduce((sum, item) => sum + item.total_cost, 0);
    const laborHours = parseFloat(document.getElementById('laborHours').value) || 0;
    const laborRate = parseFloat(document.getElementById('laborRate').value) || 125;
    const markup = parseFloat(settings.markup_percent) || 30;

    const materialsWithMarkup = materialsTotal * (1 + markup / 100);
    const laborCost = laborHours * laborRate;
    const subtotal = materialsWithMarkup + laborCost;

    document.getElementById('materialsCost').textContent = `$${materialsWithMarkup.toFixed(2)}`;
    document.getElementById('laborCost').textContent = `$${laborCost.toFixed(2)}`;
    document.getElementById('subtotal').textContent = `$${subtotal.toFixed(2)}`;
    document.getElementById('total').textContent = `$${subtotal.toFixed(2)}`;
}

function showAddItemModal() {
    document.getElementById('itemCategory').value = 'gates';
    document.getElementById('itemCustomDesc').value = '';
    document.getElementById('itemQty').value = '1';
    document.getElementById('itemUnit').value = 'each';
    document.getElementById('itemCost').value = '0';
    loadCategoryMaterials();
    openModal('itemModal');
}

async function loadCategoryMaterials() {
    const category = document.getElementById('itemCategory').value;
    const response = await fetch(`/api/materials?category=${category}`);
    const data = await response.json();

    const select = document.getElementById('itemMaterial');
    select.innerHTML = data.map(m => `<option value="${m.id}" data-unit="${m.unit}" data-cost="${m.cost}">${m.name}</option>`).join('');

    if (data.length > 0) {
        onMaterialSelect();
    }
}

function onMaterialSelect() {
    const select = document.getElementById('itemMaterial');
    const option = select.options[select.selectedIndex];
    if (option) {
        document.getElementById('itemUnit').value = option.dataset.unit || 'each';
        document.getElementById('itemCost').value = option.dataset.cost || '0';
    }
}

function addItem() {
    const select = document.getElementById('itemMaterial');
    const customDesc = document.getElementById('itemCustomDesc').value.trim();
    const description = customDesc || (select.options[select.selectedIndex]?.text || '');

    if (!description) {
        showToast('Select a material or enter description', 'error');
        return;
    }

    const qty = parseFloat(document.getElementById('itemQty').value) || 1;
    const unitCost = parseFloat(document.getElementById('itemCost').value) || 0;

    quoteItems.push({
        category: document.getElementById('itemCategory').value,
        description,
        quantity: qty,
        unit: document.getElementById('itemUnit').value,
        unit_cost: unitCost,
        total_cost: qty * unitCost
    });

    renderItems();
    updateSummary();
    closeModal('itemModal');
}

// ============== Materials / Price List ==============

async function loadCategories() {
    const response = await fetch('/api/materials/categories');
    const categories = await response.json();

    const select = document.getElementById('categoryFilter');
    if (select) {
        select.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(c => {
            select.innerHTML += `<option value="${c}">${formatValue(c)}</option>`;
        });
    }
}

async function loadMaterials() {
    const category = document.getElementById('categoryFilter')?.value || '';
    const url = category ? `/api/materials?category=${category}` : '/api/materials';
    const response = await fetch(url);
    materials = await response.json();
    renderMaterialsList();
}

function renderMaterialsList() {
    const container = document.getElementById('materialsList');
    if (materials.length === 0) {
        container.innerHTML = '<p class="empty-message">No materials found</p>';
        return;
    }

    container.innerHTML = materials.map(m => `
        <div class="material-row">
            <div class="material-info">
                <div class="material-name">${m.name}</div>
                <div class="material-details">
                    ${formatValue(m.category)} | ${m.unit} | $${m.cost.toFixed(2)} | ${((m.markup - 1) * 100).toFixed(0)}% markup
                    ${m.supplier ? ` | ${m.supplier}` : ''}
                </div>
            </div>
            <div class="row-actions">
                <button class="btn btn-small btn-secondary" onclick="editMaterial(${m.id})">Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteMaterial(${m.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function showMaterialModal(materialId = null) {
    document.getElementById('editMaterialId').value = materialId || '';
    document.getElementById('materialModalTitle').textContent = materialId ? 'Edit Material' : 'New Material';

    if (materialId) {
        const m = materials.find(x => x.id == materialId);
        if (m) {
            document.getElementById('materialCategory').value = m.category;
            document.getElementById('materialName').value = m.name;
            document.getElementById('materialUnit').value = m.unit;
            document.getElementById('materialCost').value = m.cost;
            document.getElementById('materialMarkup').value = ((m.markup - 1) * 100).toFixed(0);
            document.getElementById('materialSupplier').value = m.supplier || '';
            document.getElementById('materialSupplierUrl').value = m.supplier_url || '';
        }
    } else {
        document.getElementById('materialCategory').value = 'misc';
        document.getElementById('materialName').value = '';
        document.getElementById('materialUnit').value = 'each';
        document.getElementById('materialCost').value = '0';
        document.getElementById('materialMarkup').value = '30';
        document.getElementById('materialSupplier').value = '';
        document.getElementById('materialSupplierUrl').value = '';
    }

    openModal('materialModal');
}

function editMaterial(id) {
    showMaterialModal(id);
}

async function saveMaterial() {
    const id = document.getElementById('editMaterialId').value;
    const markupPercent = parseFloat(document.getElementById('materialMarkup').value) || 30;

    const data = {
        category: document.getElementById('materialCategory').value,
        name: document.getElementById('materialName').value,
        unit: document.getElementById('materialUnit').value,
        cost: parseFloat(document.getElementById('materialCost').value) || 0,
        markup: 1 + (markupPercent / 100),
        supplier: document.getElementById('materialSupplier').value,
        supplier_url: document.getElementById('materialSupplierUrl').value
    };

    if (!data.name) {
        showToast('Name is required', 'error');
        return;
    }

    const url = id ? `/api/materials/${id}` : '/api/materials';
    const method = id ? 'PUT' : 'POST';

    await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    closeModal('materialModal');
    loadMaterials();
    loadCategories();
    showToast('Material saved');
}

async function deleteMaterial(id) {
    if (!confirm('Delete this material?')) return;

    await fetch(`/api/materials/${id}`, { method: 'DELETE' });
    loadMaterials();
    showToast('Material deleted');
}

// ============== Supplier Price Check ==============

async function checkPrice() {
    const url = document.getElementById('priceCheckUrl').value.trim();
    if (!url) {
        showToast('Enter a product URL', 'error');
        return;
    }

    document.getElementById('priceCheckResult').innerHTML = '<p>Checking price...</p>';

    try {
        const response = await fetch('/api/price-check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.error) {
            document.getElementById('priceCheckResult').innerHTML = `<p style="color: var(--danger);">${data.error}</p>`;
        } else {
            document.getElementById('priceCheckResult').innerHTML = `
                <div class="price-result">
                    <div class="price-result-info">
                        <h4>${data.product_name}</h4>
                        <p>$${data.price.toFixed(2)} - ${data.supplier}</p>
                    </div>
                    <button class="btn btn-primary" onclick="addPriceToList('${data.product_name.replace(/'/g, "\\'")}', ${data.price}, '${data.supplier}', '${url}')">Add to Price List</button>
                </div>
            `;
        }
    } catch (e) {
        document.getElementById('priceCheckResult').innerHTML = '<p style="color: var(--danger);">Error checking price</p>';
    }
}

function addPriceToList(name, cost, supplier, url) {
    document.getElementById('editMaterialId').value = '';
    document.getElementById('materialModalTitle').textContent = 'New Material';
    document.getElementById('materialCategory').value = 'misc';
    document.getElementById('materialName').value = name.substring(0, 100);
    document.getElementById('materialUnit').value = 'each';
    document.getElementById('materialCost').value = cost;
    document.getElementById('materialMarkup').value = '30';
    document.getElementById('materialSupplier').value = supplier;
    document.getElementById('materialSupplierUrl').value = url;
    openModal('materialModal');
}

function openSupplier(supplier) {
    const product = prompt('Enter product to search:');
    if (!product) return;

    const urls = {
        homedepot: `https://www.homedepot.com/s/${encodeURIComponent(product)}`,
        lowes: `https://www.lowes.com/search?searchTerm=${encodeURIComponent(product)}`,
        tractorsupply: `https://www.tractorsupply.com/tsc/search/${encodeURIComponent(product)}`,
        walmart: `https://www.walmart.com/search?q=${encodeURIComponent(product)}`
    };

    window.open(urls[supplier], '_blank');
}

// ============== Settings ==============

async function loadSettings() {
    const response = await fetch('/api/settings');
    settings = await response.json();

    document.getElementById('companyName').value = settings.company_name || '';
    document.getElementById('companyAddress').value = settings.company_address || '';
    document.getElementById('companyPhone').value = settings.company_phone || '';
    document.getElementById('companyEmail').value = settings.company_email || '';
    document.getElementById('companyLicense').value = settings.company_license || '';
    document.getElementById('settingsLaborRate').value = settings.labor_rate || '125';
    document.getElementById('settingsMarkup').value = settings.markup_percent || '30';
    document.getElementById('settingsTaxRate').value = settings.tax_rate || '0';
    document.getElementById('settingsQuotePrefix').value = settings.quote_prefix || 'GQ';
    document.getElementById('settingsTerms').value = settings.quote_terms || '';

    // Update quote form labor rate
    document.getElementById('laborRate').value = settings.labor_rate || '125';
}

async function saveSettings() {
    const data = {
        company_name: document.getElementById('companyName').value,
        company_address: document.getElementById('companyAddress').value,
        company_phone: document.getElementById('companyPhone').value,
        company_email: document.getElementById('companyEmail').value,
        company_license: document.getElementById('companyLicense').value,
        labor_rate: document.getElementById('settingsLaborRate').value,
        markup_percent: document.getElementById('settingsMarkup').value,
        tax_rate: document.getElementById('settingsTaxRate').value,
        quote_prefix: document.getElementById('settingsQuotePrefix').value,
        quote_terms: document.getElementById('settingsTerms').value
    };

    await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    settings = data;
    showToast('Settings saved');
}

// ============== Utilities ==============

function openModal(id) {
    document.getElementById(id).classList.add('open');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('open');
}

function formatValue(value) {
    if (!value) return '';
    return value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// Update summary when labor inputs change
document.getElementById('laborHours')?.addEventListener('input', updateSummary);
document.getElementById('laborRate')?.addEventListener('input', updateSummary);
