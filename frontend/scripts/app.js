document.addEventListener("DOMContentLoaded", () => {
  const btnTraductor = document.querySelector(".btn-traductor");
  const seccionTraductor = document.getElementById("traductor");
  const contenido = document.getElementById("contenido");

  let currentStream = null; //  guardamos el stream de la cámara para detenerlo luego

  // Mostrar traductor (por si lo llaman desde botón en nav)
  btnTraductor.addEventListener("click", (e) => {
    e.preventDefault();
    contenido.innerHTML = "";
    contenido.appendChild(seccionTraductor);
    seccionTraductor.classList.remove("oculto");
    inicializarFormulario(); // inicializamos eventos
  });

  function inicializarFormulario() {
    const limpiarBtn = seccionTraductor.querySelector(".limpiarBtn");
    const textarea = seccionTraductor.querySelector("textarea");
    const seniasBtn = seccionTraductor.querySelector(".seniasPalabrasBtn");
    const columnaIzquierda = seccionTraductor.querySelector(".traductor-form");
    const salidaOriginal = seccionTraductor.querySelector(".traductor-output"); // salida fija

    if (limpiarBtn) {
      limpiarBtn.onclick = (e) => {
        e.preventDefault();
        textarea.value = "";
      };
    }

    if (seniasBtn) {
      seniasBtn.onclick = (e) => {
        e.preventDefault();

        //  Ocultar la salida original
        if (salidaOriginal) salidaOriginal.style.display = "none";

        columnaIzquierda.classList.add("senias-ui");

        columnaIzquierda.innerHTML = `
          <div class="traductor-output">
            <div class="pantalla">
              <video id="videoCamara" autoplay playsinline></video>
              <div id="textoSalida" class="texto-salida">Aquí aparecerá el texto...</div>
            </div>
          </div>

          <div class="botones">
            <button class="btn activarCamaraBtn">Activar cámara</button>
            <button class="btn volverBtn">Palabras a Señas</button>
          </div>
        `;

        const activarCamaraBtn = columnaIzquierda.querySelector(".activarCamaraBtn");
        const volverBtn = columnaIzquierda.querySelector(".volverBtn");
        const video = columnaIzquierda.querySelector("#videoCamara");
        const textoSalida = columnaIzquierda.querySelector("#textoSalida");

        //  Manejar encendido/apagado de la cámara
        activarCamaraBtn.onclick = async () => {
          if (!currentStream) {
            // Encender cámara
            try {
              currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
              video.srcObject = currentStream;
              textoSalida.textContent = "Esperando señas...";
              activarCamaraBtn.textContent = "Detener cámara";
            } catch (err) {
              console.error("Error al acceder a la cámara:", err);
              textoSalida.textContent = "No se pudo acceder a la cámara.";
            }
          } else {
            // Apagar cámara
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
            video.srcObject = null;
            textoSalida.textContent = "Cámara detenida.";
            activarCamaraBtn.textContent = "Activar cámara";
          }
        };

        volverBtn.onclick = () => {
          //  Detener la cámara si está activa
          if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
          }

          // Mostrar de nuevo la salida original
          if (salidaOriginal) salidaOriginal.style.display = "";

          columnaIzquierda.classList.remove("senias-ui");
          columnaIzquierda.innerHTML = `
            <textarea placeholder="Ingrese frase a traducir..."></textarea>

            <div class="instructions">
              <p>Palabras de contexto separadas por (,)</p>
            </div>

            <select>
              <option>Colombia</option>
              <option>México</option>
              <option>Argentina</option>
              <option>Chile</option>
            </select>

            <div class="botones">
              <button class="btn traducirBtn">Traducir</button>
              <button class="btn limpiarBtn">Limpiar</button>
              <button class="btn seniasPalabrasBtn">Señas a palabras</button>
            </div>
          `;
          inicializarFormulario(); // volvemos a enganchar eventos
        };
      };
    }
  }

  // inicializar por defecto si el traductor ya está en pantalla
  inicializarFormulario();
});
