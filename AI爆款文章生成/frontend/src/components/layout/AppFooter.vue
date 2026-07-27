<template>
  <a-layout-footer class="footer">
    <div class="footer-content">
      <p class="copyright">
        <span class="footer-brand">墨笔</span>
        &mdash; AI 驱动的内容创作平台 &copy; 2026
      </p>
    </div>
  </a-layout-footer>
</template>

<style scoped>
.footer {
  background: var(--color-background);
  text-align: center;
  padding: 24px 20px;
  margin-top: 0;
  border-top: 1px solid var(--color-border);
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
}

.copyright {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.footer-brand {
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  color: var(--color-primary-dark);
}
</style>
