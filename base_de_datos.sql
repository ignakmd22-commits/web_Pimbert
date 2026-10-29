-- Base de datos del sitio Pimbert · Deslizora (SQLite)
-- Se crea sola la primera vez que se inicia servidor.py

PRAGMA foreign_keys = ON;

CREATE TABLE paginas (
  id INTEGER PRIMARY KEY,
  archivo TEXT NOT NULL UNIQUE,               -- ej.: producto.html
  orden INTEGER NOT NULL,                     -- 0 = inicio
  titulo_menu TEXT NOT NULL,                  -- texto en menú superior y migas de pan
  titulo_pie TEXT NOT NULL,                   -- texto en el pie de página
  en_menu INTEGER NOT NULL DEFAULT 0 CHECK (en_menu IN (0,1)),
  es_boton INTEGER NOT NULL DEFAULT 0 CHECK (es_boton IN (0,1)),
  tarjeta_titulo TEXT,                        -- NULL = no sale como tarjeta en el index
  tarjeta_descripcion TEXT,
  tarjeta_enlace TEXT
);
CREATE TABLE caracteristicas (id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, icono_svg TEXT NOT NULL, titulo TEXT NOT NULL, descripcion TEXT NOT NULL);
CREATE TABLE puntos_resumen (id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, titulo TEXT NOT NULL);
CREATE TABLE pasos (id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, titulo TEXT NOT NULL, descripcion TEXT NOT NULL);
CREATE TABLE materiales (id INTEGER PRIMARY KEY, grupo TEXT NOT NULL CHECK (grupo IN ('prototipo','fabricacion')), orden INTEGER NOT NULL, simbolo TEXT NOT NULL, nombre TEXT NOT NULL, descripcion TEXT NOT NULL);
CREATE TABLE ambitos_uso (id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, icono_svg TEXT NOT NULL, titulo TEXT NOT NULL, descripcion TEXT NOT NULL, etiqueta TEXT NOT NULL);
CREATE TABLE preguntas_frecuentes (id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, pregunta TEXT NOT NULL, respuesta TEXT NOT NULL);
CREATE TABLE tipos_espacio (id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE consultas (
  id INTEGER PRIMARY KEY,
  creada_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,   -- UTC
  nombre TEXT NOT NULL,
  contacto TEXT NOT NULL,                               -- email o teléfono
  institucion TEXT,
  ancho TEXT,
  alto TEXT,
  tipo_espacio_id INTEGER NOT NULL REFERENCES tipos_espacio(id),
  detalles TEXT,
  estado TEXT NOT NULL DEFAULT 'nueva' CHECK (estado IN ('nueva','atendida'))
);

INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('index.html', 0, 'Inicio', 'Inicio', 0, 0, NULL, NULL, NULL);
INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('producto.html', 1, 'El producto', 'El producto', 1, 0, 'El producto', 'Características y ventajas del sistema de borrado corredizo.', 'Conocer el producto');
INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('funcionamiento.html', 2, 'Funcionamiento', 'Funcionamiento', 1, 0, 'Cómo funciona', 'Descubrí cómo las guías acompañan el movimiento del borrador.', 'Descubrir cómo funciona');
INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('materiales.html', 3, 'Materiales', 'Materiales', 1, 0, 'Materiales', 'Conocé los componentes que forman el sistema Deslizora.', 'Ver materiales');
INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('ambitos-de-uso.html', 4, 'Ámbitos de uso', 'Ámbitos de uso', 1, 0, 'Ámbitos de uso', 'Espacios educativos y de trabajo donde una pizarra es parte del día a día.', 'Ver ámbitos de uso');
INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('proyecto.html', 5, 'El proyecto', 'El proyecto', 1, 0, 'El proyecto', 'La necesidad que inspiró la idea y el desarrollo del prototipo.', 'Conocer el proyecto');
INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('preguntas-frecuentes.html', 6, 'Preguntas frecuentes', 'Preguntas frecuentes', 0, 0, 'Preguntas frecuentes', 'Respuestas sobre adaptación, compatibilidad, materiales y precio.', 'Leer las preguntas');
INSERT INTO paginas (archivo, orden, titulo_menu, titulo_pie, en_menu, es_boton, tarjeta_titulo, tarjeta_descripcion, tarjeta_enlace) VALUES ('consulta.html', 7, 'Consultar', 'Consulta', 1, 1, 'Consultas', 'Prepará una consulta con los datos aproximados de tu pizarra.', 'Preparar una consulta');
INSERT INTO caracteristicas (orden, icono_svg, titulo, descripcion) VALUES (1, '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3.5 2"></path>', 'Más rapidez', 'El recorrido horizontal busca reducir el tiempo que lleva borrar la superficie completa de la pizarra.');
INSERT INTO caracteristicas (orden, icono_svg, titulo, descripcion) VALUES (2, '<path d="M8 11V5a2 2 0 0 1 4 0v5-7a2 2 0 0 1 4 0v8-5a2 2 0 0 1 4 0v9a6 6 0 0 1-6 6h-2c-2 0-3.3-.8-4.5-2.2L4 14a2 2 0 0 1 3-2l2 2"></path>', 'Uso más cómodo', 'El sistema está pensado para evitar estiramientos y movimientos repetitivos del brazo al alcanzar distintas zonas.');
INSERT INTO caracteristicas (orden, icono_svg, titulo, descripcion) VALUES (3, '<path d="M4 5h16v14H4zM7 9h10M7 12h10M7 15h6"></path><path d="m8 2 4 3 4-3"></path>', 'Borrado parejo', 'El contacto uniforme del borrador busca dejar menos marcas y residuos visibles a lo largo del recorrido.');
INSERT INTO caracteristicas (orden, icono_svg, titulo, descripcion) VALUES (4, '<path d="M4 7h16M4 17h16M7 4v6M17 14v6"></path><path d="M9 12h6"></path>', 'Adaptación a medida', 'Las guías y la estructura del borrador se dimensionan según las medidas de la pizarra donde se instalarían.');
INSERT INTO puntos_resumen (orden, titulo) VALUES (1, 'Desplazamiento lateral guiado');
INSERT INTO puntos_resumen (orden, titulo) VALUES (2, 'Guías en la parte superior e inferior');
INSERT INTO puntos_resumen (orden, titulo) VALUES (3, 'Una pasada a lo largo de la superficie');
INSERT INTO puntos_resumen (orden, titulo) VALUES (4, 'Componentes reparables o reemplazables');
INSERT INTO pasos (orden, titulo, descripcion) VALUES (1, 'Se adapta a la pizarra', 'Se toman las medidas y se preparan las guías para cubrir el ancho y el alto útiles de la superficie.');
INSERT INTO pasos (orden, titulo, descripcion) VALUES (2, 'Se desliza el borrador', 'Las ruedas o deslizadores siguen las guías superior e inferior y ayudan a mantener el recorrido alineado.');
INSERT INTO pasos (orden, titulo, descripcion) VALUES (3, 'Se limpia la superficie', 'El material de borrado recorre la pizarra para retirar los restos de tiza o marcador de forma uniforme.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('prototipo', 1, '⚙', 'Ruedas pequeñas para riel', 'Permiten guiar el movimiento del mecanismo a lo largo de los carriles.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('prototipo', 2, '▤', 'Madera de abedul', 'Se utilizó para elaborar los rieles ubicados en la parte superior e inferior del pizarrón.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('prototipo', 3, '▧', 'Tela de rejilla amarilla', 'Material utilizado temporalmente en el prototipo durante el desarrollo.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('prototipo', 4, '◫', 'Gomaespuma', 'Se incorporó para ayudar al balance del borrador sin generar demasiada fricción.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('prototipo', 5, '⌁', 'Tornillos, clavos y madera blanca', 'Elementos de unión y material usado para representar la superficie de una pizarra real en la maqueta.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('fabricacion', 1, '▤', 'Guías de aluminio', 'Perfiles anodizados tipo U o guías lineales livianas para mantener la trayectoria.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('fabricacion', 2, '▥', 'Estructura del borrador', 'Perfil de aluminio extruido o madera tratada de baja densidad, como MDF o kiri.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('fabricacion', 3, '▨', 'Fieltro o microfibra lavable', 'Paño de fieltro o microfibra lavable, con fijación mediante abrojo si el diseño lo requiere.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('fabricacion', 4, '⚙', 'Rodamientos o deslizadores', 'Poleas de nylon con rulemanes de bolas o patines de teflón para un desplazamiento suave.');
INSERT INTO materiales (grupo, orden, simbolo, nombre, descripcion) VALUES ('fabricacion', 5, '↔', 'Sistema de presión', 'Resortes de compresión o bandas de goma para mantener el material de borrado en contacto con la pizarra.');
INSERT INTO ambitos_uso (orden, icono_svg, titulo, descripcion, etiqueta) VALUES (1, '<path d="M3 21h18M5 21V7l7-4 7 4v14M9 10h.01M15 10h.01M9 14h.01M15 14h.01M10 21v-4h4v4"></path>', 'Escuelas y colegios', 'Para aulas de nivel secundario, especialmente escuelas técnicas, donde el pizarrón se utiliza durante muchas clases.', 'Educación');
INSERT INTO ambitos_uso (orden, icono_svg, titulo, descripcion, etiqueta) VALUES (2, '<rect height="13" rx="2" width="18" x="3" y="4"></rect><path d="M8 21h8M12 17v4M7 9h10M7 12h6"></path>', 'Institutos y talleres de formación', 'En espacios donde docentes o instructores explican procedimientos, desarrollan ejercicios y reutilizan la pizarra.', 'Capacitación');
INSERT INTO ambitos_uso (orden, icono_svg, titulo, descripcion, etiqueta) VALUES (3, '<rect height="13" rx="2" width="18" x="3" y="7"></rect><path d="M8 7V4h8v3M7 11h10M7 15h4M12 20v2"></path>', 'Empresas y salas de reunión', 'Para reuniones de equipo, planificación y explicación de ideas en ambientes de trabajo que utilizan pizarras.', 'Entornos corporativos');
INSERT INTO preguntas_frecuentes (orden, pregunta, respuesta) VALUES (1, '¿Deslizora tiene una medida única?', 'No. La propuesta contempla adaptar el sistema a la medida de la pizarra. Para definir una instalación, es necesario conocer su ancho, alto y tipo de marco.');
INSERT INTO preguntas_frecuentes (orden, pregunta, respuesta) VALUES (2, '¿Se puede utilizar en pizarras existentes?', 'El proyecto busca adaptarse a pizarras convencionales con marcos de madera o metálicos. La compatibilidad debe comprobarse tomando las medidas y revisando cada estructura.');
INSERT INTO preguntas_frecuentes (orden, pregunta, respuesta) VALUES (3, '¿Cuál es el precio de venta?', 'El precio comercial dependerá de las dimensiones de la pizarra, los materiales elegidos y las características de la instalación. Para definirlo, será necesario evaluar cada caso.');
INSERT INTO preguntas_frecuentes (orden, pregunta, respuesta) VALUES (4, '¿Se pueden elegir otros materiales?', 'Sí. Además de los materiales del prototipo, se pueden evaluar opciones como guías de aluminio, fieltro o microfibra lavable y distintos sistemas de deslizamiento, según la pizarra y el uso previsto.');
INSERT INTO tipos_espacio (orden, nombre) VALUES (1, 'Aula escolar');
INSERT INTO tipos_espacio (orden, nombre) VALUES (2, 'Instituto o taller de formación');
INSERT INTO tipos_espacio (orden, nombre) VALUES (3, 'Oficina o sala de reunión');
INSERT INTO tipos_espacio (orden, nombre) VALUES (4, 'Otro espacio');
