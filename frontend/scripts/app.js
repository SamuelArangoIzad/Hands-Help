document.addEventListener("DOMContentLoaded", () => {
  const btnTraductor = document.querySelector(".btn-traductor");
  const seccionTraductor = document.getElementById("traductor");
  const contenido = document.getElementById("contenido");

  // ====== Backend ======
  const API_BASE = "https://hands-help.onrender.com";

  // ====== Estado cámara ======
  let currentStream = null;
  let canvasOverlay = null;
  let ctx = null;

  // Mostrar traductor al hacer clic en el botón del navbar
  btnTraductor.addEventListener("click", (e) => {
    e.preventDefault();
    contenido.innerHTML = "";
    contenido.appendChild(seccionTraductor);
    seccionTraductor.classList.remove("oculto");
    inicializarFormulario();
  });

  function inicializarFormulario() {
    const columnaIzquierda = seccionTraductor.querySelector(".traductor-form");
    const salidaOriginal = seccionTraductor.querySelector(".traductor-output");
    const instrucciones = columnaIzquierda.querySelector(".instructions");

    const textarea = columnaIzquierda.querySelector("textarea");
    const select = columnaIzquierda.querySelector("select");
    const traducirBtn = columnaIzquierda.querySelector(".traducirBtn");
    const limpiarBtn = columnaIzquierda.querySelector(".limpiarBtn");
    const seniasBtn = columnaIzquierda.querySelector(".seniasPalabrasBtn");

    // Limpiar texto
    if (limpiarBtn) {
      limpiarBtn.onclick = (e) => {
        e.preventDefault();
        textarea.value = "";
      };
    }

    // ====== Señas -> Palabras (cámara) ======
    if (seniasBtn) {
      seniasBtn.onclick = (e) => {
        e.preventDefault();
        if (salidaOriginal) salidaOriginal.style.display = "none";

        // Oculta elementos del modo palabras->señas
        textarea.style.display = "none";
        select.style.display = "none";
        traducirBtn.style.display = "none";
        limpiarBtn.style.display = "none";
        seniasBtn.style.display = "none";
        if (instrucciones) instrucciones.style.display = "none";

        columnaIzquierda.classList.add("senias-ui");

        // --- Video + canvas ---
        let videoContainer = columnaIzquierda.querySelector(".video-container");
        if (!videoContainer) {
          videoContainer = document.createElement("div");
          videoContainer.classList.add("video-container");
          videoContainer.style.position = "relative";

          const video = document.createElement("video");
          video.id = "videoCamara";
          video.autoplay = true;
          video.playsInline = true;
          videoContainer.appendChild(video);

          const canvas = document.createElement("canvas");
          canvas.id = "canvasOverlay";
          canvas.style.position = "absolute";
          canvas.style.left = "0";
          canvas.style.top = "0";
          videoContainer.appendChild(canvas);

          columnaIzquierda.appendChild(videoContainer);
        }
        videoContainer.style.display = "block";

        // Texto de estado
        let textoSalida = columnaIzquierda.querySelector("#textoSalida");
        if (!textoSalida) {
          textoSalida = document.createElement("div");
          textoSalida.id = "textoSalida";
          textoSalida.className = "texto-salida";
          textoSalida.textContent = "Esperando señas...";
          columnaIzquierda.appendChild(textoSalida);
        } else {
          textoSalida.style.display = "block";
          textoSalida.textContent = "Esperando señas...";
        }

        // Botones de cámara
        let activarCamaraBtn = columnaIzquierda.querySelector(".activarCamaraBtn");
        if (!activarCamaraBtn) {
          activarCamaraBtn = document.createElement("button");
          activarCamaraBtn.className = "btn activarCamaraBtn";
          activarCamaraBtn.textContent = "Activar cámara";
          columnaIzquierda.appendChild(activarCamaraBtn);
        }
        let volverBtn = columnaIzquierda.querySelector(".volverBtn");
        if (!volverBtn) {
          volverBtn = document.createElement("button");
          volverBtn.className = "btn volverBtn";
          volverBtn.textContent = "Volver";
          columnaIzquierda.appendChild(volverBtn);
        }
        activarCamaraBtn.style.display = "inline-block";
        volverBtn.style.display = "inline-block";

        const video = videoContainer.querySelector("#videoCamara");
        canvasOverlay = videoContainer.querySelector("#canvasOverlay");
        ctx = canvasOverlay.getContext("2d");

        // Layout: cámara izquierda / controles derecha
        let leyout = columnaIzquierda.querySelector(".senias-layout");
        if (!leyout) {
          leyout = document.createElement("div");
          leyout.className = "senias-layout";

          // izquierda: video
          leyout.appendChild(videoContainer);

          // derecha: controles
          const controls = document.createElement("div");
          controls.className = "controls-panel";
          const title = document.createElement("h4");
          title.textContent = "Controles";
          controls.appendChild(title);
          controls.appendChild(activarCamaraBtn);
          controls.appendChild(volverBtn);

          leyout.appendChild(controls);
          leyout.insertBefore(textoSalida, controls);

          columnaIzquierda.appendChild(leyout);
        } else {
          leyout.style.display = "grid";
          const controls = leyout.querySelector(".controls-panel");
          if (controls && !controls.contains(activarCamaraBtn)) controls.appendChild(activarCamaraBtn);
          if (controls && !controls.contains(volverBtn)) controls.appendChild(volverBtn);
        }

        // --- Cámara on/off ---
        activarCamaraBtn.onclick = async () => {
          if (!currentStream) {
            try {
              // Wake-up del backend para evitar 502 en la primera llamada
              await fetch(`${API_BASE}/`, { mode: "cors" }).catch(() => {});

              currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
              video.srcObject = currentStream;

              video.onloadedmetadata = () => {
                canvasOverlay.width = video.videoWidth || 640;
                canvasOverlay.height = video.videoHeight || 360;
                canvasOverlay.style.width = "100%";
                canvasOverlay.style.height = "100%";
                procesarFrame(video, canvasOverlay, textoSalida);
              };

              activarCamaraBtn.textContent = "Detener cámara";
              textoSalida.textContent = "Esperando señas...";
            } catch (err) {
              console.error("Error al acceder a la cámara:", err);
              textoSalida.textContent = "No se pudo acceder a la cámara.";
            }
          } else {
            detenerCamara(video, activarCamaraBtn, textoSalida);
          }
        };

        volverBtn.onclick = () => {
          detenerCamara(video, activarCamaraBtn, textoSalida);
          if (salidaOriginal) salidaOriginal.style.display = "";

          // Restaurar modo palabras->señas
          textarea.style.display = "block";
          select.style.display = "block";
          traducirBtn.style.display = "inline-block";
          limpiarBtn.style.display = "inline-block";
          seniasBtn.style.display = "inline-block";
          if (instrucciones) instrucciones.style.display = "block";

          videoContainer.style.display = "none";
          activarCamaraBtn.style.display = "none";
          volverBtn.style.display = "none";
          textoSalida.style.display = "none";
        };
      };
    }

    // ====== Palabras -> Señas (imágenes) ======
    if (traducirBtn) {
      traducirBtn.onclick = async () => {
        const texto = textarea.value.trim();
        if (!texto) return alert("Escribe algo para traducir");
        const pantalla = salidaOriginal.querySelector(".pantalla");
        pantalla.innerHTML = "";

        try {
          const res = await fetch(`${API_BASE}/traducir`, {
            method: "POST",
            mode: "cors",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto })
          });
          const data = await res.json();

          data.senas.forEach((s, i) => {
            setTimeout(() => {
              pantalla.innerHTML = `<img src="${s.url}" alt="Seña ${s.letra}" style="max-width:200px;">`;
            }, i * 2500);
          });
        } catch (err) {
          console.error(err);
          alert("Error conectando al traductor");
        }
      };
    }
  }

  // ====== Loop de frames hacia el backend ======
  function procesarFrame(video, canvas, textoSalida) {
    if (!ctx || !currentStream) return;

    // 1) Baja resolución para reducir payload (≈360p)
    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 360;
    const targetW = 360;
    const targetH = Math.round((vh / vw) * targetW);

    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = targetW;
    tempCanvas.height = targetH;
    const tempCtx = tempCanvas.getContext("2d", { willReadFrequently: true });
    tempCtx.drawImage(video, 0, 0, targetW, targetH);

    // 2) Comprime el JPEG
    const frameBase64 = tempCanvas.toDataURL("image/jpeg", 0.45);

    const t0 = performance.now();
    fetch(`${API_BASE}/detectar-senas`, {
      method: "POST",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ frame: frameBase64 })
    })
      .then(res => res.json())
      .then(data => {
        const t1 = performance.now();
        if (data.debug) {
          console.log(`hands=${data.debug.hands} | ${data.debug.ms}ms server | ${Math.round(t1 - t0)}ms RTT`);
        }

        // Dibuja retorno del servidor sólo si viene (puede desactivarse en backend)
        if (data.frame) {
          const img = new Image();
          img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          };
          img.src = data.frame;
        }

        if (data.letra) {
          textoSalida.textContent = `Seña detectada: ${data.letra}`;
        }

        // 3) Throttle para no saturar Render Free (~2.2 FPS)
        if (currentStream) setTimeout(() => procesarFrame(video, canvas, textoSalida), 450);
      })
      .catch(err => {
        console.error("detectar-senas error:", err);
        // Backoff si falló
        if (currentStream) setTimeout(() => procesarFrame(video, canvas, textoSalida), 1000);
      });
  }

  function detenerCamara(video, boton, textoSalida) {
    if (currentStream) currentStream.getTracks().forEach(track => track.stop());
    currentStream = null;
    video.srcObject = null;
    if (canvasOverlay && ctx) ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);
    if (boton) boton.textContent = "Activar cámara";
    if (textoSalida) textoSalida.textContent = "Esperando señas...";
  }

  // Inicializa al cargar Home
  inicializarFormulario();
});
