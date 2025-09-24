document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.querySelector('.table-search-input');
  const searchForm = document.querySelector('.table-search-box');
  const budgetFilter = document.querySelector('.budget-status-filter');

  if (!searchInput || !searchForm) return;

  let searchTimeout;
  let isSearching = false;

  searchInput.addEventListener('input', function() {
    if (isSearching) return;
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function() {
      isSearching = true;
      const icon = document.querySelector('.table-search-icon');
      if (icon) icon.className = 'fas fa-spinner fa-spin table-search-icon';
      try { searchForm.submit(); } finally { isSearching = false; }
    }, 500);
  });

  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && this.value) {
      this.value = '';
      if (searchTimeout) clearTimeout(searchTimeout);
      searchForm.submit();
    }
  });

  if (budgetFilter) {
    budgetFilter.addEventListener('change', function() {
      searchForm.submit();
    });
  }
});


