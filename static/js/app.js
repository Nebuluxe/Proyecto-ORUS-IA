document.addEventListener('DOMContentLoaded', () => {
    
    // --- LÓGICA DE DIBUJO ROI ---
    const canvas = document.getElementById('roi-canvas');
    const ctx = canvas.getContext('2d');
    const btnDrawRoi = document.getElementById('btn-draw-roi');
    const videoStream = document.getElementById('video-stream');
    
    let isDrawingMode = false;
    let points = [];
    let scaleX = 1;
    let scaleY = 1;

    // Sincronizar tamaño del canvas con el video
    function resizeCanvas() {
        // Asumiendo que el stream nativo de OpenCV suele ser 640x480
        // Ajustamos la escala para mapear clics
        const rect = videoStream.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        
        // La cámara por defecto envía 640x480, deberíamos escalar los puntos a la resolución real
        scaleX = 640 / rect.width;
        scaleY = 480 / rect.height;
        redraw();
    }
    
    window.addEventListener('resize', resizeCanvas);
    videoStream.onload = resizeCanvas;

    btnDrawRoi.addEventListener('click', () => {
        isDrawingMode = !isDrawingMode;
        if (isDrawingMode) {
            btnDrawRoi.innerHTML = '<i class="ph ph-check"></i> Guardar ROI';
            btnDrawRoi.classList.replace('primary', 'secondary');
            btnDrawRoi.style.borderColor = 'var(--success)';
            btnDrawRoi.style.color = 'var(--success)';
            points = [];
            canvas.style.cursor = 'crosshair';
            redraw();
        } else {
            // Modo guardar
            btnDrawRoi.innerHTML = '<i class="ph ph-bounding-box"></i> Dibujar Zona (ROI)';
            btnDrawRoi.classList.replace('secondary', 'primary');
            btnDrawRoi.style.borderColor = 'transparent';
            btnDrawRoi.style.color = 'white';
            canvas.style.cursor = 'default';
            
            if (points.length >= 3) {
                // Enviar puntos a la API escalados a 640x480
                const scaledPoints = points.map(p => [Math.round(p.x * scaleX), Math.round(p.y * scaleY)]);
                fetch('/api/roi', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ puntos: scaledPoints })
                }).then(res => res.json())
                  .then(data => {
                      alert(data.message || "ROI Guardada");
                      points = [];
                      redraw();
                  });
            } else if (points.length > 0) {
                alert("Se requieren al menos 3 puntos para formar un polígono.");
                points = [];
                redraw();
            }
        }
    });

    canvas.addEventListener('click', (e) => {
        if (!isDrawingMode) return;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        points.push({x, y});
        redraw();
    });

    // Clic derecho para deshacer
    canvas.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (!isDrawingMode) return;
        points.pop();
        redraw();
    });

    function redraw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (points.length > 0) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
            if (isDrawingMode && points.length > 2) {
                // Cerrar para visualización
                ctx.lineTo(points[0].x, points[0].y);
            }
            
            ctx.strokeStyle = '#06b6d4'; // accent
            ctx.lineWidth = 2;
            ctx.stroke();

            // Puntos
            ctx.fillStyle = '#ef4444'; // danger
            points.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
                ctx.fill();
            });
        }
    }

    // --- LÓGICA DE REGISTRO DE RESIDENTES ---
    const btnTrain = document.getElementById('btn-train');
    const modalTrain = document.getElementById('modal-train');
    const inputNombre = document.getElementById('input-nombre');
    const submitTrain = document.getElementById('submit-train');

    window.closeModal = () => {
        modalTrain.classList.remove('active');
        inputNombre.value = '';
    };

    btnTrain.addEventListener('click', () => {
        modalTrain.classList.add('active');
        inputNombre.focus();
    });

    submitTrain.addEventListener('click', () => {
        const nombre = inputNombre.value.trim();
        if (nombre) {
            submitTrain.disabled = true;
            submitTrain.innerHTML = '<i class="ph ph-spinner ph-spin"></i> Iniciando...';
            
            fetch('/api/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre })
            }).then(res => res.json())
              .then(data => {
                  alert("¡Párate frente a la cámara! El sistema capturará tus movimientos.");
                  closeModal();
              }).finally(() => {
                  submitTrain.disabled = false;
                  submitTrain.innerHTML = 'Iniciar Captura';
              });
        }
    });

    // --- LÓGICA DE LOGS (POLLING) ---
    function fetchLogs() {
        fetch('/api/logs')
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById('logs-container');
                if (data.error) {
                    console.error("Error fetching logs:", data.error);
                    return;
                }
                
                if (data.length === 0) {
                    container.innerHTML = '<div class="log-placeholder">Sin alertas registradas</div>';
                    return;
                }

                container.innerHTML = '';
                data.forEach(log => {
                    // Formatear timestamp
                    let timeStr = log.timestamp;
                    const card = document.createElement('div');
                    card.className = 'log-card';
                    card.innerHTML = `
                        <div class="log-header">
                            <span>ID: #${log.objeto_id}</span>
                            <span>${timeStr}</span>
                        </div>
                        <div class="log-title">ALERTA DE INTRUSO</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted); word-break: break-all;">
                            ${log.foto_path}
                        </div>
                    `;
                    container.appendChild(card);
                });
            })
            .catch(err => console.error(err));
    }

    // Inicializar
    setInterval(fetchLogs, 5000); // Poll cada 5s
    fetchLogs();

    // --- NAVEGACIÓN Y VISTAS ---
    const navMonitor = document.getElementById('nav-monitor');
    const navResidents = document.getElementById('nav-residents');
    const navConfig = document.getElementById('nav-config');
    const secMonitor = document.getElementById('section-monitor');
    const secResidents = document.getElementById('section-residents');
    const secConfig = document.getElementById('section-config');

    function hideAll() {
        secMonitor.classList.add('hidden');
        secResidents.classList.add('hidden');
        secConfig.classList.add('hidden');
        navMonitor.classList.remove('active');
        navResidents.classList.remove('active');
        navConfig.classList.remove('active');
    }

    navMonitor.addEventListener('click', () => {
        hideAll();
        secMonitor.classList.remove('hidden');
        navMonitor.classList.add('active');
    });

    navResidents.addEventListener('click', () => {
        hideAll();
        secResidents.classList.remove('hidden');
        navResidents.classList.add('active');
        loadResidents();
    });

    navConfig.addEventListener('click', () => {
        hideAll();
        secConfig.classList.remove('hidden');
        navConfig.classList.add('active');
        loadConfig();
    });

    // Evento del botón secundario de residentes
    const btnTrainAlt = document.getElementById('btn-train-alt');
    if (btnTrainAlt) {
        btnTrainAlt.addEventListener('click', () => {
            modalTrain.classList.add('active');
            inputNombre.focus();
        });
    }

    // --- CONFIGURACIÓN ---
    const btnSaveConfig = document.getElementById('btn-save-config');
    const inputCooldown = document.getElementById('input-cooldown');
    const inputCamera = document.getElementById('input-camera');

    function loadConfig() {
        fetch('/api/config')
            .then(res => res.json())
            .then(data => {
                inputCooldown.value = data.cooldown_seconds;
                inputCamera.value = data.camera_index;
            });
    }

    if (btnSaveConfig) {
        btnSaveConfig.addEventListener('click', () => {
            fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cooldown_seconds: inputCooldown.value,
                    camera_index: inputCamera.value
                })
            }).then(res => res.json())
              .then(data => {
                  alert(data.message);
              });
        });
    }

    // --- GESTIÓN DE RESIDENTES ---
    const residentsList = document.getElementById('residents-list');

    function loadResidents() {
        fetch('/api/residents')
            .then(res => res.json())
            .then(data => {
                residentsList.innerHTML = '';
                if (!data.residentes || data.residentes.length === 0) {
                    residentsList.innerHTML = '<p style="color:var(--text-muted); grid-column: 1/-1; text-align:center;">No hay residentes registrados.</p>';
                    return;
                }
                data.residentes.forEach(name => {
                    const card = document.createElement('div');
                    card.className = 'resident-card';
                    card.innerHTML = `
                        <i class="ph ph-user-circle resident-icon"></i>
                        <div class="resident-name">${name}</div>
                        <button class="btn-delete" data-name="${name}">Eliminar Todos los Registros</button>
                    `;
                    residentsList.appendChild(card);
                });

                // Attach delete events
                document.querySelectorAll('.btn-delete').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const nameToDelete = e.target.getAttribute('data-name');
                        if (confirm(`¿Seguro que deseas borrar la base facial de ${nameToDelete}? La IA lo detectará como intruso.`)) {
                            deleteResident(nameToDelete);
                        }
                    });
                });
            });
    }

    function deleteResident(name) {
        fetch('/api/residents', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre: name })
        }).then(res => res.json())
          .then(data => {
              if (data.success) {
                  alert(`Residente ${name} borrado exitosamente.`);
                  loadResidents(); // recargar
              } else {
                  alert(data.error);
              }
          });
    }

});
