# RehabWeb-Api

Backend API para la webapp de fisioterapia **RehabWeb**, construido con Django REST Framework y MySQL.

---

## 📋 Tabla de Tecnologías

| Tecnología | Versión |
|---|---|
| Python | 3.12+ |
| Django | 6.0.2 |
| Django REST Framework | 3.16.1 |
| django-cors-headers | 4.9.0 |
| django-filter | 25.2 |
| mysqlclient | 2.2.8 |
| MySQL (XAMPP) | 8.0+ |

---

## 🚀 Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd RehabWeb-Api
```

### 2. Crear y activar entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

1. Asegúrate de que **MySQL** esté corriendo (por ejemplo, via XAMPP).
2. Crea la base de datos `rehab_db`:

```sql
CREATE DATABASE rehab_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Verifica que la configuración en `RehabWeb_API/settings.py` coincida con tu entorno:
   - `USER`: `root`
   - `PASSWORD`: `` (vacío por defecto en XAMPP)
   - `HOST`: `127.0.0.1`
   - `PORT`: `3306`

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 7. Iniciar servidor de desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://127.0.0.1:8000/`

---

## 📁 Estructura del proyecto

```
RehabWeb-Api/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
└── RehabWeb_API/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── wsgi.py
    ├── asgi.py
    ├── admin.py
    ├── models.py
    ├── serializers.py
    ├── permissions.py
    ├── views/
    │   └── __init__.py
    └── migrations/
        └── __init__.py
```

---

## 🌿 Estrategia de Branching

Este proyecto sigue una estrategia de branching por equipos con revisión en staging.

### Diagrama de flujo

```
main ← staging ← equipo/{nombre} ← dev/{nombre-desarrollador}
```

### Ramas principales

| Rama | Propósito | ¿Quién hace merge aquí? |
|------|-----------|-------------------------|
| `main` | Producción estable. Solo código probado y aprobado. | Líder del proyecto tras aprobación en staging |
| `staging` | Rama de integración y pruebas. Aquí se valida que todos los equipos funcionen juntos. | Líderes de equipo |
| `equipo/equipo-1` | Rama principal del Equipo 1. | Los desarrolladores del Equipo 1 |
| `equipo/equipo-2` | Rama principal del Equipo 2. | Los desarrolladores del Equipo 2 |
| `equipo/equipo-3` | Rama principal del Equipo 3. | Los desarrolladores del Equipo 3 |
| `equipo/equipo-4` | Rama principal del Equipo 4. | Los desarrolladores del Equipo 4 |
| `equipo/equipo-5` | Rama principal del Equipo 5. | Los desarrolladores del Equipo 5 |
| `equipo/equipo-6` | Rama principal del Equipo 6. | Los desarrolladores del Equipo 6 |
| `dev/{nombre}` | Rama personal de cada desarrollador (ej: `dev/juan-lopez`). | El desarrollador individual |

### Flujo de trabajo

1. **Cada desarrollador** trabaja en su rama personal `dev/{nombre}`.
2. Al terminar su sprint o tarea asignada, el desarrollador crea un **Pull Request** hacia la rama de su equipo `equipo/{nombre}`.
3. El **líder de equipo** revisa el PR y hace merge a `equipo/{nombre}`.
4. Cuando el equipo completa su sprint, el líder crea un **Pull Request** de `equipo/{nombre}` → `staging`.
5. En `staging` se ejecutan **pruebas de integración** para verificar que todo funcione en conjunto.
6. Si las pruebas pasan, se crea un **Pull Request** de `staging` → `main`.

### Convención de commits

Usar el formato **Conventional Commits**:

```
<tipo>(<alcance>): <descripción corta>

[cuerpo opcional]
```

#### Tipos permitidos

| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato, punto y coma faltantes, etc. (no cambia lógica) |
| `refactor` | Refactorización de código (no agrega ni corrige) |
| `test` | Agregar o corregir tests |
| `chore` | Tareas de mantenimiento (dependencias, configs) |

#### Ejemplos

```
feat(auth): agregar endpoint de login con JWT
fix(formulario): corregir validación de email en registro
docs(readme): actualizar instrucciones de instalación
refactor(servicios): extraer lógica de HTTP a servicio base
chore(deps): actualizar Angular a v20.3
```

### Reglas importantes

> ⚠️ **NUNCA** hacer push directo a `main` o `staging`.
>
> ⚠️ **SIEMPRE** crear Pull Requests para cualquier merge entre ramas.
>
> ⚠️ Antes de crear un PR, hacer `git pull` de la rama destino para evitar conflictos.
