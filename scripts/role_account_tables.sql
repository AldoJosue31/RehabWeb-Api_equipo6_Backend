-- Script MySQL basado en "Diagrama de Clases.pdf" para extender auth_user
-- con tablas de rol. Django conserva auth_user para login/token.

CREATE TABLE IF NOT EXISTS RehabWeb_API_terapeutaprofile (
  id CHAR(32) NOT NULL PRIMARY KEY,
  usuario_id BIGINT NOT NULL UNIQUE,
  especialidad VARCHAR(120) NOT NULL,
  numero_licencia VARCHAR(80) NOT NULL UNIQUE,
  CONSTRAINT fk_terapeuta_usuario
    FOREIGN KEY (usuario_id) REFERENCES auth_user(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS RehabWeb_API_perfilclinico (
  id CHAR(32) NOT NULL PRIMARY KEY,
  diagnostico_principal VARCHAR(180) NOT NULL,
  historial_medico LONGTEXT NOT NULL,
  nivel_movilidad VARCHAR(20) NOT NULL,
  restricciones LONGTEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS RehabWeb_API_pacienteprofile (
  id CHAR(32) NOT NULL PRIMARY KEY,
  usuario_id BIGINT NOT NULL UNIQUE,
  terapeuta_id CHAR(32) NULL,
  perfil_clinico_id CHAR(32) NULL UNIQUE,
  fecha_nacimiento DATE NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'activo',
  estrategia_validacion VARCHAR(120) NOT NULL DEFAULT 'Libre',
  estrategia_progreso VARCHAR(120) NOT NULL DEFAULT 'Por rutinas',
  CONSTRAINT fk_paciente_usuario
    FOREIGN KEY (usuario_id) REFERENCES auth_user(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_paciente_terapeuta
    FOREIGN KEY (terapeuta_id) REFERENCES RehabWeb_API_terapeutaprofile(id)
    ON DELETE SET NULL,
  CONSTRAINT fk_paciente_perfil_clinico
    FOREIGN KEY (perfil_clinico_id) REFERENCES RehabWeb_API_perfilclinico(id)
    ON DELETE SET NULL
);
