document.addEventListener("DOMContentLoaded", () => {
  const contenido = document.getElementById("contenido");
  const enlaces = document.querySelectorAll(".nav-links a");

  const secciones = {
    inicio: `
      <section id="inicio" class="section inicio-container">
        <div class="inicio-texto">
          <h1>Herramienta Tecnológica para ayuda humanitaria y consentimiento social</h1>
          <p>El objetivo de esta página es netamente educativa y contribuir a la construcción
             de un mundo mejor. Nos esforzamos juntos como sociedad para convertirnos en un entorno
             dedicado al desarrollo de herramientas para la ayuda de otros.
          </p>
        </div>
        <div class="inicio-imagen">
          <img src="../database/img/Logo.png" alt="Logo Practical Hands">
        </div>
      </section>
    `,
    nosotros: `
    <section id="nosotros" class="section">
  <div class="nosotros-container">
    <div class="nosotros-item">
      <h3>Visión</h3>
      <p>
        Convertirnos en un referente de solidaridad y humanismo, fomentando la empatía, la inclusión y el respeto hacia todas las personas. 
        Buscamos ser reconocidos universalmente por nuestro compromiso con la comunicación accesible y por contribuir a un desarrollo 
        sostenible que inspire a las futuras generaciones a construir un mundo más justo, empático y humano.
      </p>
    </div>

    <div class="nosotros-item">
      <h3>Misión</h3>
      <p>
        Como estudiante, busco promover la interacción, el respeto y el acogimiento de diferentes personas, 
        sin importar sus condiciones físicas, culturales o sociales. Mi misión es fomentar la empatía en la comunicación, 
        impulsando el uso de la tecnología como una herramienta de inclusión y apoyo mutuo.  
        Aspiro a que este proyecto sirva como un puente para que más individuos puedan expresarse, comprenderse y 
        reconocerse en la diversidad, contribuyendo así a la construcción de una sociedad más justa, solidaria y humana.
      </p>
    </div>

    <div class="nosotros-item">
      <h3>Filosofía</h3>
      <ul>
        <li>Amor por el ser humano</li>
        <li>Respeto ante las diferencias</li>
        <li>Actuar por amor al humano y su entorno natural</li>
        <li>Reconocer un poder universal que nos inspira a dar lo mejor de nosotros</li>
      </ul>
    </div>
  </div>
</section>

    `,
    herramientas: `
      <section id="herramientas" class="section">
      <div class="herramientas-texto">
        <h2>Herramientas</h2>
        <p>
          Las herramientas que implementamos en este proyecto son de uso libre y de código abierto, 
          pensadas para fomentar la innovación y la colaboración. 
          Nos apoyamos en un entorno de programación basado en Debian, con distribución gratuita 
          para que cualquier persona interesada pueda aprender, mejorar y contribuir.  
          Creemos que la programación es un medio para construir un mundo mejor, promoviendo el 
          conocimiento compartido y la solidaridad digital
        </p>
        </div>

        <div class="logos-herramientas">
          <img src="../database/img/python.png" alt="Python" title="Python">
          <img src="../database/img/javascript.png" alt="JavaScript" title="JavaScript">
          <img src="../database/img/html.png" alt="HTML" title="HTML5">
          <img src="../database/img/css.png" alt="CSS" title="CSS3">
          <img src="../database/img/github.png" alt="GitHub" title="GitHub">
          <img src="../database/img/debian.png" alt="Debian" title="Debian Linux">
        </div>
      </section>
    `,
    contacto: `
    <section id="contacto" class="section">
        <div class="contact-card">
        <div class="contact-info">
        <h3>Samuel Arango Díaz</h3>
        <p>Ingeniería de Sistemas e Informática</p>
           <a href="https://www.linkedin.com/in/samuel-arango-diaz-a6a06a293/" target="_blank" class="linkedin-btn">
             Ver en LinkedIn
           </a>
           </div>
           </div>
    </section>
    `
  };

enlaces.forEach(enlace => {
    enlace.addEventListener("click", (e) => {
      e.preventDefault();
      const id = enlace.getAttribute("href").substring(1);

      // 1. Fade-out
      contenido.classList.remove("show");
      contenido.classList.add("fade");

      setTimeout(() => {


        if (id === "traductor"){

          //Mostrar la sección traaductor que ya existe
          const seccionTraductor = document.getElementById("traductor");
          contenido.innerHTML = "";
          contenido.appendChild(seccionTraductor);
          seccionTraductor.classList.remove("oculto");

        }

        else{

          // 2. Cambiar contenido
          contenido.innerHTML = secciones[id] || "<p>Sección en construcción</p>";

          //3 Volver a mostrar (fade-in)
          requestAnimationFrame(() => {
            contenido.classList.add("show");
          });

          // Marcar enlace activo
          enlaces.forEach(a => a.classList.remove("active"));
          enlace.classList.add("active");
        }

      }, 400); // tiempo de fade-out antes de reemplazar
    });
  });

  // Mostrar inicio por defecto
  contenido.classList.add("fade", "show");
});
