# 🤖 Guía de Colaboración: Omnibot-TMR

chabales, para mantener el repositorio limpio y evitar conflictos de código, sigan estos pasos en orden cada vez que vayan a trabajar.

## 1. Configuración Inicial

Primero, clona el repositorio y entra a la carpeta del proyecto:

```Bash
git clone https://github.com/BrandonPerez915/omnibot-TMR
cd omnibot-TMR
```

## 2. Gestión de Branches (Ramas)

Importante: Nadie trabaja sobre main. Cada quien tiene su espacio asignado:

- Cesar: Tu rama es control
- Ivan: Tu rama es communication

Para crear y moverte a tu rama, usa:

```Bash
# Cambia 'nombre-branch' por control o communication según te toque
git checkout -b nombre-branch
```

## 3. Desarrollo y Organización

Una vez en tu rama, localiza la carpeta que te corresponde (/control o /communication):

- Si ya tienes código: Cópialo dentro de tu carpeta respectiva.
- Si vas a empezar de cero: Crea tus archivos directamente ahí.

💡 Tip: No modifiques archivos fuera de tu carpeta asignada a menos que sea estrictamente necesario.

4. Subir Cambios (Workflow de Git)
   Cuando estés listo para subir tus avances, sigue este flujo:

### Paso A: Preparar archivos (Add)

```Bash
# Para subir una carpeta completa:
git add nombre_carpeta/

# Para subir un archivo específico:
git add nombre_archivo.cpp
```

### Paso B: Confirmar cambios (Commit)

Escribe mensajes claros para saber qué se hizo:

```Bash
git commit -m "Escribe aquí qué agregaste o qué corregiste"
```

### Paso C: Publicar en el repo (Push)

```Bash
# Recuerda usar el nombre de tu rama (control o communication)
git push origin nombre_branch 5. Revisión y Pull Requests
```

Una vez que hagas el push, me llegará la notificación del Pull Request. Yo revisaré el código para integrarlo a la rama principal.

# ⚠️ Notas Importantes

Documentación: Siéntanse libres de usar este README para anotar estructuras de datos (ej. qué recibe la ESP32), pines usados o librerías extra.

Limpieza: No suban archivos binarios, ejecutables o carpetas temporales de compilación, modifiquen el gitignore si es necesario
