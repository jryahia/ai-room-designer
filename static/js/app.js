// ---------- Upload ----------
const dropZone = document.getElementById('drop-zone');
const photoInput = document.getElementById('room-photo');
const dropContent = document.getElementById('drop-content');
const dropPreview = document.getElementById('drop-preview');
const previewImg = document.getElementById('preview-img');
const previewName = document.getElementById('preview-name');

function previewFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewName.textContent = file.name;
        dropContent.classList.add('hidden');
        dropPreview.classList.remove('hidden');
        dropZone.classList.add('has-image');
    };
    reader.readAsDataURL(file);
}

function removePhoto() {
    photoInput.value = '';
    previewImg.src = '';
    dropPreview.classList.add('hidden');
    dropContent.classList.remove('hidden');
    dropZone.classList.remove('has-image');
}

if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            photoInput.files = e.dataTransfer.files;
            previewFile(e.dataTransfer.files[0]);
        }
    });
    photoInput.addEventListener('change', () => {
        if (photoInput.files.length) previewFile(photoInput.files[0]);
    });
}

// ---------- Custom theme ----------
const customWrap = document.getElementById('custom-theme-input');
document.querySelectorAll('input[name="theme"]').forEach((radio) => {
    radio.addEventListener('change', () => {
        const isCustom = radio.value === 'custom' && radio.checked;
        customWrap.classList.toggle('hidden', !isCustom);
        if (isCustom) document.getElementById('custom-theme-text').focus();
    });
});

// ---------- Live area / volume ----------
const dims = ['width_m', 'length_m', 'height_m'].map((id) => document.getElementById(id));
function updateArea() {
    const [w, l, h] = dims.map((el) => parseFloat(el.value) || 0);
    document.getElementById('area-display').textContent = `${(w * l).toFixed(1)} m²`;
    document.getElementById('volume-display').textContent = `${(w * l * h).toFixed(1)} m³`;
}
if (dims.every(Boolean)) {
    dims.forEach((el) => el.addEventListener('input', updateArea));
    updateArea();
}

// ---------- Submit ----------
const designForm = document.getElementById('design-form');
if (designForm) {
    designForm.addEventListener('submit', (e) => {
        if (!photoInput.files.length) {
            e.preventDefault();
            dropZone.classList.add('error');
            dropZone.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => dropZone.classList.remove('error'), 1500);
            return;
        }
        document.getElementById('loading-overlay').classList.remove('hidden');
        document.getElementById('submit-btn').disabled = true;
        const steps = [1, 2, 3, 4].map((n) => document.getElementById(`step-${n}`));
        steps[0].classList.add('active');
        let i = 0;
        const timer = setInterval(() => {
            steps[i].classList.replace('active', 'done');
            i += 1;
            if (i >= steps.length) return clearInterval(timer);
            steps[i].classList.add('active');
        }, 9000);
    });
}

// ---------- Results ----------
function toggleDesign(index) {
    const detail = document.getElementById(`detail-${index}`);
    const label = document.getElementById(`expand-text-${index}`);
    const opening = detail.classList.contains('hidden');
    document.querySelectorAll('.card-detail').forEach((d) => d.classList.add('hidden'));
    document.querySelectorAll('[id^="expand-text-"]').forEach((l) => { l.textContent = 'Vedi Dettagli / View Details'; });
    if (opening) {
        detail.classList.remove('hidden');
        label.textContent = 'Chiudi / Close';
    }
}

function switchLang(index, lang) {
    const other = lang === 'it' ? 'en' : 'it';
    document.getElementById(`rationale-${lang}-${index}`).classList.remove('hidden');
    document.getElementById(`rationale-${other}-${index}`).classList.add('hidden');
    const buttons = document.querySelectorAll(`#detail-${index} .tab-btn`);
    buttons.forEach((b, i) => b.classList.toggle('active', (i === 0) === (lang === 'it')));
}

async function pickDesign(index) {
    const btn = document.getElementById(`pick-btn-${index}`);
    const design = (window.DESIGN_DATA || []).find((d) => d.index === index) || {};
    const d = window.DIMENSIONS || {};
    btn.disabled = true;
    try {
        const res = await fetch('/api/pick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                room_type: window.ROOM_TYPE,
                theme: window.THEME,
                width_m: d.width,
                length_m: d.length,
                height_m: d.height,
                selected_design_index: index,
                design_summary: {
                    name_en: design.name_en,
                    name_it: design.name_it,
                    style_tags: design.style_tags,
                    total_cost: design.total_cost,
                },
            }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        btn.classList.add('hidden');
        document.getElementById(`pick-thanks-${index}`).classList.remove('hidden');
    } catch (err) {
        btn.disabled = false;
        console.error(err);
    }
}
