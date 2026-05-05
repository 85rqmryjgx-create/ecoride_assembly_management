// ── TOAST ───────────────────���──────────────────────
function showToast(msg, type = 'default') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = `toast-msg ${type}`;
  const icons = { success: '✅', error: '❌', default: 'ℹ️' };
  t.innerHTML = `<span>${icons[type] || icons.default}</span> ${msg}`;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── STEP TIMER ─────────────────────────────────────
class StepTimer {
  constructor(executionId, estimatedMinutes, container) {
    this.executionId = executionId;
    this.estimatedMinutes = estimatedMinutes;
    this.container = container;
    this.elapsed = 0;
    this.running = false;
    this.interval = null;
    this.startTs = null;

    this.display = container.querySelector('.timer-display');
    this.startBtn = container.querySelector('.btn-timer-start');
    this.saveBtn = container.querySelector('.btn-timer-save');
    this.minutesInput = container.querySelector('.hidden-minutes');
    this.stepCard = container.closest('.step-card');

    this.startBtn.addEventListener('click', () => this.toggle());
    if (this.saveBtn) this.saveBtn.addEventListener('click', () => this.save());
  }

  toggle() {
    this.running ? this.stop() : this.start();
  }

  start() {
    this.running = true;
    this.startTs = Date.now() - (this.elapsed * 1000);
    this.stepCard.classList.add('active');
    this.startBtn.classList.add('running');
    this.startBtn.innerHTML = '<span>⏹</span> Parar';

    this.interval = setInterval(() => {
      this.elapsed = Math.floor((Date.now() - this.startTs) / 1000);
      const mins = Math.floor(this.elapsed / 60);
      const secs = this.elapsed % 60;
      this.display.textContent = `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
      if (this.minutesInput) this.minutesInput.value = mins || 1;

      // Color feedback
      if (mins > this.estimatedMinutes) {
        this.display.classList.add('overtime');
        this.display.classList.remove('running');
      } else {
        this.display.classList.add('running');
        this.display.classList.remove('overtime');
      }
    }, 1000);
  }

  stop() {
    clearInterval(this.interval);
    this.running = false;
    this.startBtn.classList.remove('running');
    this.startBtn.innerHTML = '<span>▶</span> Retomar';
    this.display.classList.remove('running');
    if (this.saveBtn) this.saveBtn.style.display = 'flex';
  }

  async save() {
    const minutes = this.minutesInput ? parseInt(this.minutesInput.value) || 1 : Math.ceil(this.elapsed / 60);
    const notesEl = this.container.querySelector('.step-notes');
    const notes = notesEl ? notesEl.value : '';

    this.saveBtn.innerHTML = '⏳';
    this.saveBtn.classList.add('saving');

    try {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
      const resp = await fetch(`/assembly/executions/${this.executionId}/save/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: `actual_minutes=${minutes}&notes=${encodeURIComponent(notes)}`,
      });

      const data = await resp.json();
      if (data.success) {
        this.stepCard.classList.remove('active');
        this.stepCard.classList.add('done');
        this.container.innerHTML = `
          <div style="display:flex;align-items:center;gap:8px;padding:4px 0">
            <span style="font-size:28px">✅</span>
            <div>
              <div style="font-weight:700;font-size:15px">${minutes} min recorded</div>
              ${notes ? `<div style="font-size:12px;color:var(--text-muted)">${notes}</div>` : ''}
            </div>
          </div>`;
        showToast('Step saved!', 'success');
        updateSessionProgress();
      } else {
        showToast('Error saving. Try again.', 'error');
        this.saveBtn.classList.remove('saving');
        this.saveBtn.innerHTML = '💾';
      }
    } catch (e) {
      showToast('Connection error.', 'error');
      this.saveBtn.classList.remove('saving');
      this.saveBtn.innerHTML = '💾';
    }
  }
}

function updateSessionProgress() {
  const total = document.querySelectorAll('.step-card').length;
  const done = document.querySelectorAll('.step-card.done').length;
  const pct = total ? Math.round((done / total) * 100) : 0;
  const fill = document.getElementById('session-progress-fill');
  const label = document.getElementById('session-progress-label');
  if (fill) fill.style.width = pct + '%';
  if (label) label.textContent = `${done} of ${total} steps (${pct}%)`;
}

// ── PHOTO PREVIEW ─────────────────────���────────────
function initPhotoPreview() {
  const input = document.getElementById('photo-input');
  const preview = document.getElementById('photo-preview');
  const previewImg = document.getElementById('preview-img');
  const removeBtn = document.getElementById('remove-photo');
  const uploadArea = document.getElementById('upload-area');

  if (!input) return;

  input.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      previewImg.src = ev.target.result;
      preview.style.display = 'block';
      uploadArea.style.display = 'none';
    };
    reader.readAsDataURL(file);
  });

  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      input.value = '';
      preview.style.display = 'none';
      uploadArea.style.display = 'block';
    });
  }
}

// ── SEVERITY SELECTOR ────────────────���────────────
function initSeveritySelector() {
  document.querySelectorAll('.severity-option').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('.severity-option').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      opt.querySelector('input').checked = true;
    });
  });
}

// ── TYPE SELECTOR ────────────��────────────────────
function initTypeSelector() {
  document.querySelectorAll('.type-option').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('.type-option').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      opt.querySelector('input').checked = true;
    });
  });
}

// ── STEP CARDS INIT ───────────────────────────────
function initStepTimers() {
  // Click on header to expand/collapse
  document.querySelectorAll('.step-header-expandable').forEach(header => {
    header.style.cursor = 'pointer';
    header.addEventListener('click', () => {
      const card = header.closest('.step-card');
      const chevron = header.querySelector('.step-chevron');
      card.classList.toggle('active');
      if (chevron) chevron.style.transform = card.classList.contains('active') ? 'rotate(180deg)' : '';
    });
  });

  // Timer + manual save
  document.querySelectorAll('.timer-container').forEach(container => {
    const execId = container.dataset.executionId;
    const estMin = parseInt(container.dataset.estimated) || 0;
    if (execId) {
      new StepTimer(execId, estMin, container);

      // Manual save (new step) or update (edit mode)
      const manualBtn = container.querySelector('.manual-save-btn');
      if (manualBtn) {
        const isEdit = container.dataset.mode === 'edit';
        const url = isEdit
          ? `/assembly/executions/${execId}/update/`
          : `/assembly/executions/${execId}/save/`;

        manualBtn.addEventListener('click', async () => {
          const input = container.querySelector('.manual-minutes');
          const minutes = parseInt(input ? input.value : 0);
          if (!minutes || minutes < 1) { showToast('Enter a valid number of minutes.', 'error'); return; }
          const notes = container.querySelector('.step-notes')?.value || '';
          manualBtn.disabled = true;
          manualBtn.innerHTML = '⏳';
          try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const resp = await fetch(url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
              body: `actual_minutes=${minutes}&notes=${encodeURIComponent(notes)}`,
            });
            const data = await resp.json();
            if (data.success) {
              const card = container.closest('.step-card');
              card.classList.remove('active');
              card.classList.add('done');
              if (!isEdit) {
                container.innerHTML = `<div style="display:flex;align-items:center;gap:8px;padding:4px 0"><span style="font-size:28px">✅</span><div><div style="font-weight:700;font-size:15px">${minutes} min recorded</div>${notes ? `<div style="font-size:12px;color:var(--text-muted)">${notes}</div>` : ''}</div></div>`;
                updateSessionProgress();
              }
              showToast(isEdit ? 'Step updated!' : 'Step saved!', 'success');
              const badge = card.querySelector('.step-number ~ div + div .badge-app');
              if (badge && isEdit) badge.textContent = `${minutes} min`;
              if (isEdit) { card.classList.remove('active'); const chevron = card.querySelector('.step-chevron'); if (chevron) chevron.style.transform = ''; }
            } else {
              showToast('Error saving.', 'error');
              manualBtn.disabled = false;
              manualBtn.innerHTML = '<i class="bi bi-floppy"></i> ' + (isEdit ? 'Update' : 'Save');
            }
          } catch (e) {
            showToast('Connection error.', 'error');
            manualBtn.disabled = false;
            manualBtn.innerHTML = '<i class="bi bi-floppy"></i> ' + (isEdit ? 'Update' : 'Save');
          }
        });
      }

      // Reset step execution
      const resetBtn = container.querySelector('.step-reset-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
          if (!confirm('Reset this step? The recorded time will be removed.')) return;
          try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const resp = await fetch(`/assembly/executions/${execId}/reset/`, {
              method: 'POST',
              headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            });
            const data = await resp.json();
            if (data.success) { showToast('Step reset.', 'success'); setTimeout(() => location.reload(), 800); }
          } catch (e) { showToast('Connection error.', 'error'); }
        });
      }
    }
  });
  updateSessionProgress();
}

// ── SESSION FINISH CONFIRM ────────────────────────
function confirmFinish(url) {
  if (confirm('Complete this assembly session?')) {
    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
    }).then(() => location.reload());
  }
}

// ── INIT ───────────────��──────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initPhotoPreview();
  initSeveritySelector();
  initTypeSelector();
  initStepTimers();

  // Auto-dismiss django messages
  document.querySelectorAll('.django-msg').forEach(el => {
    setTimeout(() => el.remove(), 3000);
  });
});
