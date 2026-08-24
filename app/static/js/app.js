/* ==========================================================================
   BankMS Neo - Modern Frontend Logic & State Management
   ========================================================================== */

const API_BASE = window.location.origin + "/api";

let currentUser = null;
let currentSummary = null;
let allTransactions = [];
let activeFilter = 'ALL';
let isBalanceHidden = false;
let cashflowChartInstance = null;
let lookupTimeout = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  checkAuth();
});

function getAuthToken() {
  return localStorage.getItem("bankms_token");
}

function setAuthToken(token) {
  if (token) {
    localStorage.setItem("bankms_token", token);
  } else {
    localStorage.removeItem("bankms_token");
  }
}

// API Request Wrapper
async function apiRequest(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const config = { method, headers };
    if (body) config.body = JSON.stringify(body);

    const res = await fetch(`${API_BASE}${endpoint}`, config);
    const data = await res.json();

    if (!res.ok) {
      if (res.status === 401 && !endpoint.includes("/auth/")) {
        logout();
        showToast("Session expired. Please sign in again.", "error");
      }
      throw new Error(data.detail || "Something went wrong with the request");
    }
    return data;
  } catch (err) {
    showToast(err.message, "error");
    throw err;
  }
}

// Event Listeners
function setupEventListeners() {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const btnSignOut = document.getElementById("btnSignOut");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("loginUsername").value;
      const password = document.getElementById("loginPassword").value;
      await handleLogin(username, password);
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("regUsername").value;
      const password = document.getElementById("regPassword").value;
      const full_name = document.getElementById("regFullName").value;
      const email = document.getElementById("regEmail").value;
      await handleRegister({ username, password, full_name, email });
    });
  }

  if (btnSignOut) {
    btnSignOut.addEventListener("click", () => {
      logout();
      showToast("Signed out successfully", "info");
    });
  }

  // Close modals when clicking backdrop
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        closeModal(overlay.id);
      }
    });
  });
}

// Check Existing Auth
async function checkAuth() {
  const token = getAuthToken();
  if (!token) {
    showAuthView();
    return;
  }

  try {
    currentUser = await apiRequest("/auth/me");
    showDashboardView();
    await fetchDashboardData();
  } catch (err) {
    logout();
  }
}

// UI State Switchers
function showAuthView() {
  document.getElementById("authSection").classList.remove("hidden");
  document.getElementById("dashboardSection").classList.add("hidden");
  document.getElementById("authNavUser").classList.add("hidden");
}

function showDashboardView() {
  document.getElementById("authSection").classList.add("hidden");
  document.getElementById("dashboardSection").classList.remove("hidden");
  document.getElementById("authNavUser").classList.remove("hidden");
}

function switchAuthTab(tab) {
  const tabLogin = document.getElementById("tabLogin");
  const tabRegister = document.getElementById("tabRegister");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");

  if (tab === "login") {
    tabLogin.classList.add("active");
    tabRegister.classList.remove("active");
    loginForm.classList.remove("hidden");
    registerForm.classList.add("hidden");
  } else {
    tabLogin.classList.remove("active");
    tabRegister.classList.add("active");
    loginForm.classList.add("hidden");
    registerForm.classList.remove("hidden");
  }
}

function fillDemoCredentials(username, password) {
  document.getElementById("loginUsername").value = username;
  document.getElementById("loginPassword").value = password;
  showToast(`Loaded demo user: ${username}`, "info");
}

// Auth Handlers
async function handleLogin(username, password) {
  try {
    const res = await apiRequest("/auth/login", "POST", { username, password });
    setAuthToken(res.access_token);
    currentUser = res.user;
    showToast(`Welcome back, ${currentUser.full_name || currentUser.username}!`, "success");
    showDashboardView();
    await fetchDashboardData();
  } catch (e) {}
}

async function handleRegister(payload) {
  try {
    const res = await apiRequest("/api/auth/register", "POST", payload);
    setAuthToken(res.access_token);
    currentUser = res.user;
    showToast(`Account created successfully! Welcome, ${currentUser.username}`, "success");
    showDashboardView();
    await fetchDashboardData();
  } catch (e) {}
}

function logout() {
  setAuthToken(null);
  currentUser = null;
  currentSummary = null;
  showAuthView();
}

// Dashboard Data
async function fetchDashboardData() {
  try {
    const summary = await apiRequest("/account/summary");
    currentSummary = summary;
    currentUser = summary.user;

    // Fetch full history
    const history = await apiRequest("/transactions/history?limit=100");
    allTransactions = history;

    renderDashboard(summary);
    renderTransactionsTable(allTransactions);
    renderCashflowChart(summary.total_inflow, summary.total_outflow, summary.balance);
  } catch (e) {}
}

function renderDashboard(summary) {
  const user = summary.user;
  
  // Navbar user
  const initials = (user.full_name || user.username).substring(0, 2).toUpperCase();
  document.getElementById("navAvatarInitials").textContent = initials;
  document.getElementById("navUsername").textContent = user.username;

  // Header & Card Name
  document.getElementById("dashFullName").textContent = user.full_name || user.username;
  document.getElementById("virtualCardHolder").textContent = (user.full_name || user.username).toUpperCase();
  
  // Account number format (e.g. 8841 0294 10)
  const acc = user.account_number || "0000000000";
  const formattedAcc = `${acc.substring(0, 4)} ${acc.substring(4, 8)} ${acc.substring(8)}`;
  document.getElementById("virtualAccNumber").textContent = formattedAcc;

  // Balance display
  updateBalanceDisplay(summary.balance);

  // Inflow & Outflow
  document.getElementById("dashTotalInflow").textContent = `+$${summary.total_inflow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  document.getElementById("dashTotalOutflow").textContent = `-$${summary.total_outflow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  
  // Modal balance preview
  document.getElementById("withdrawMaxBalance").textContent = `$${summary.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function updateBalanceDisplay(amount) {
  const balanceEl = document.getElementById("dashBalanceDisplay");
  if (isBalanceHidden) {
    balanceEl.textContent = "••••••";
  } else {
    balanceEl.textContent = amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
}

function toggleBalanceVisibility() {
  isBalanceHidden = !isBalanceHidden;
  const btn = document.getElementById("toggleBalanceBtn");
  btn.textContent = isBalanceHidden ? "👁️ Show" : "👁️ Hide";
  if (currentSummary) {
    updateBalanceDisplay(currentSummary.balance);
  }
}

function copyAccountNumber() {
  if (!currentUser) return;
  navigator.clipboard.writeText(currentUser.account_number);
  showToast(`Account Number copied: ${currentUser.account_number}`, "success");
}

// Transaction Ledger Rendering
function renderTransactionsTable(transactions) {
  const tbody = document.getElementById("txnTableBody");
  const emptyState = document.getElementById("txnEmptyState");
  tbody.innerHTML = "";

  let filtered = transactions;
  if (activeFilter !== 'ALL') {
    filtered = filtered.filter(t => t.transaction_type === activeFilter);
  }

  const query = (document.getElementById("txnSearchInput").value || "").toLowerCase().trim();
  if (query) {
    filtered = filtered.filter(t => 
      t.reference_id.toLowerCase().includes(query) ||
      (t.note && t.note.toLowerCase().includes(query)) ||
      (t.sender_username && t.sender_username.toLowerCase().includes(query)) ||
      (t.receiver_username && t.receiver_username.toLowerCase().includes(query))
    );
  }

  if (filtered.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  filtered.forEach((txn) => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-deposit";
    let isPositive = false;
    let peerDisplay = "";

    if (txn.transaction_type === "DEPOSIT") {
      badgeClass = "badge-deposit";
      isPositive = true;
      peerDisplay = "Self (Cash In)";
    } else if (txn.transaction_type === "WITHDRAWAL") {
      badgeClass = "badge-withdrawal";
      isPositive = false;
      peerDisplay = "Self (Cash Out)";
    } else if (txn.transaction_type === "TRANSFER") {
      badgeClass = "badge-transfer";
      if (txn.receiver_id === currentUser.id) {
        isPositive = true;
        peerDisplay = `From @${txn.sender_username}`;
      } else {
        isPositive = false;
        peerDisplay = `To @${txn.receiver_username}`;
      }
    }

    const formattedDate = new Date(txn.created_at).toLocaleString([], {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });

    const amountFormatted = `${isPositive ? '+' : '-'}$${txn.amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    const amountColorClass = isPositive ? 'text-emerald' : 'text-rose';
    const balanceAfterStr = txn.balance_after !== null && txn.balance_after !== undefined ? `$${txn.balance_after.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-";

    tr.innerHTML = `
      <td><span class="font-mono" style="font-size: 0.775rem; color: #94a3b8;">${txn.reference_id}</span></td>
      <td><span class="txn-type-badge ${badgeClass}">${txn.transaction_type}</span></td>
      <td><strong style="color: #f1f5f9;">${peerDisplay}</strong></td>
      <td style="color: var(--text-muted);">${txn.note || '-'}</td>
      <td style="color: var(--text-dim); font-size: 0.8rem;">${formattedDate}</td>
      <td class="font-mono ${amountColorClass}" style="font-weight: 700;">${amountFormatted}</td>
      <td class="font-mono" style="color: #cbd5e1;">${balanceAfterStr}</td>
    `;
    tbody.appendChild(tr);
  });
}

function setTxnFilter(type, element) {
  activeFilter = type;
  document.querySelectorAll(".filter-chip").forEach(chip => chip.classList.remove("active"));
  element.classList.add("active");
  renderTransactionsTable(allTransactions);
}

function filterTransactions() {
  renderTransactionsTable(allTransactions);
}

// Chart.js Visualization
function renderCashflowChart(inflow, outflow, balance) {
  const ctx = document.getElementById('cashflowChart');
  if (!ctx) return;

  if (cashflowChartInstance) {
    cashflowChartInstance.destroy();
  }

  cashflowChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Total Balance', 'Total Deposits (Inflow)', 'Total Spending (Outflow)'],
      datasets: [{
        label: 'USD ($)',
        data: [balance, inflow, outflow],
        backgroundColor: [
          'rgba(59, 130, 246, 0.75)',
          'rgba(16, 185, 129, 0.75)',
          'rgba(244, 63, 94, 0.75)'
        ],
        borderColor: [
          '#3b82f6',
          '#10b981',
          '#f43f5e'
        ],
        borderWidth: 1.5,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` $${context.raw.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#94a3b8',
            callback: (val) => `$${val.toLocaleString()}`
          }
        }
      }
    }
  });
}

// Live Recipient Validation Debounce
function debounceLookupRecipient() {
  clearTimeout(lookupTimeout);
  const input = document.getElementById("transferRecipient").value.trim();
  const box = document.getElementById("recipientLookupBox");
  const text = document.getElementById("recipientLookupText");
  const badge = document.getElementById("recipientLookupBadge");

  if (!input) {
    box.classList.add("hidden");
    return;
  }

  box.classList.remove("hidden");
  text.textContent = "Verifying account...";
  badge.textContent = "Checking";
  badge.className = "txn-type-badge";

  lookupTimeout = setTimeout(async () => {
    try {
      const res = await apiRequest(`/account/lookup/${encodeURIComponent(input)}`);
      if (res.is_self) {
        text.textContent = `Cannot transfer to yourself (${res.username})`;
        badge.textContent = "Invalid";
        badge.className = "txn-type-badge badge-withdrawal";
      } else {
        text.textContent = `Recipient: ${res.full_name || res.username} (@${res.username})`;
        badge.textContent = "Verified ✓";
        badge.className = "txn-type-badge badge-deposit";
      }
    } catch (e) {
      text.textContent = "No matching account found";
      badge.textContent = "Not Found";
      badge.className = "txn-type-badge badge-withdrawal";
    }
  }, 400);
}

// Modal Handlers & Actions
function openModal(id) {
  document.getElementById(id).classList.add("active");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("active");
}

async function handleDeposit(e) {
  e.preventDefault();
  const amount = parseFloat(document.getElementById("depositAmount").value);
  const note = document.getElementById("depositNote").value;

  try {
    await apiRequest("/transactions/deposit", "POST", { amount, note });
    showToast(`Successfully deposited $${amount.toFixed(2)}`, "success");
    closeModal("depositModal");
    document.getElementById("depositForm").reset();
    await fetchDashboardData();
  } catch (e) {}
}

async function handleWithdraw(e) {
  e.preventDefault();
  const amount = parseFloat(document.getElementById("withdrawAmount").value);
  const note = document.getElementById("withdrawNote").value;

  try {
    await apiRequest("/transactions/withdraw", "POST", { amount, note });
    showToast(`Successfully withdrew $${amount.toFixed(2)}`, "success");
    closeModal("withdrawModal");
    document.getElementById("withdrawForm").reset();
    await fetchDashboardData();
  } catch (e) {}
}

async function handleTransfer(e) {
  e.preventDefault();
  const recipient = document.getElementById("transferRecipient").value.trim();
  const amount = parseFloat(document.getElementById("transferAmount").value);
  const note = document.getElementById("transferNote").value;

  try {
    await apiRequest("/transactions/transfer", "POST", { recipient, amount, note });
    showToast(`Successfully sent $${amount.toFixed(2)} to ${recipient}!`, "success");
    closeModal("transferModal");
    document.getElementById("transferForm").reset();
    document.getElementById("recipientLookupBox").classList.add("hidden");
    await fetchDashboardData();
  } catch (e) {}
}

// CSV Statement Exporter
function exportTransactionsCSV() {
  if (!allTransactions || allTransactions.length === 0) {
    showToast("No transactions to export", "info");
    return;
  }

  const headers = ["Reference ID", "Type", "Sender", "Receiver", "Amount", "Note", "Date", "Balance After"];
  const rows = allTransactions.map(t => [
    t.reference_id,
    t.transaction_type,
    t.sender_username || "Self",
    t.receiver_username || "Self",
    t.amount,
    `"${(t.note || '').replace(/"/g, '""')}"`,
    new Date(t.created_at).toISOString(),
    t.balance_after !== null ? t.balance_after : ""
  ]);

  const csvContent = "data:text/csv;charset=utf-8," 
    + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `bankms_statement_${currentUser.username}_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showToast("Account statement downloaded as CSV", "success");
}

// Toast Notifications System
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icon = type === "success" ? "✅" : (type === "error" ? "⚠️" : "ℹ️");
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(20px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
