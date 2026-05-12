// Drag & drop upload
const uploadZone = document.getElementById('upload-zone');
const photoInput = document.getElementById('room-photo');
const photoPreview = document.getElementById('photo-preview');

if (uploadZone) {
    uploadZone.addEventListener('click', () => photoInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            photoInput.files = e.dataTransfer.files;
            previewFile(e.dataTransfer.files[0]);
        }
    });
    
    photoInput.addEventListener('change', () => {
        if (photoInput.files.length) previewFile(photoInput.files[0]);
    });
}

function previewFile(file) {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        photoPreview.src = e.target.result;
        photoPreview.style.display = 'block';
        uploadZone.classList.add('has-image');
    };
    reader.readAsDataURL(file);
}

// Form submission
const designForm = document.getElementById('design-form');
if (designForm) {
    designForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(designForm);
        const loadingOverlay = document.getElementById('loading-overlay');
        const steps = document.querySelectorAll('.step');
        
        loadingOverlay.classList.add('active');
        
        // Animate steps
        const stepNames = ['analyzing', 'trends', 'designs', 'renders', 'complete'];
        for (let i = 0; i < stepNames.length; i++) {
            await new Promise(r => setTimeout(r, 800));
            document.getElementById(`step-${stepNames[i]}`).classList.add('active');
            if (i > 0) document.getElementById(`step-${stepNames[i-1]}`).classList.remove('active');
            document.getElementById(`step-${stepNames[i]}`).classList.add('done');
        }
        
        try {
            const response = await fetch('/design', { method: 'POST', body: formData });
            const html = await response.text();
            document.open();
            document.write(html);
            document.close();
        } catch (err) {
            loadingOverlay.classList.remove('active');
            alert('Error: ' + err.message);
        }
    });
}

// Design card expand/collapse
function toggleDesign(index) {
    const detail = document.getElementById(`detail-${index}`);
    const allDetails = document.querySelectorAll('.design-detail');
    allDetails.forEach(d => { if (d !== detail) d.classList.remove('open'); });
    detail.classList.toggle('open');
}

// Pick a design
async function pickDesign(index) {
    const btn = document.querySelector(`#detail-${index} .btn-success`);
    if (btn) btn.textContent = '✓ Salvato!';
    try {
        await fetch('/api/pick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ design_index: index })
        });
    } catch (err) { console.error(err); }
}
