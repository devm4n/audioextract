#!/bin/bash

# Configuración de colores para la consola
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin color

echo -e "${BLUE}=== Iniciando instalación local de Ponytail para OpenCode ===${NC}"

# 1. Crear directorios necesarios de OpenCode en el proyecto
echo -e "${YELLOW}[1/6] Creando estructura de carpetas local...${NC}"
mkdir -p .opencode/plugins
mkdir -p .opencode/command

# 2. Clonar el repositorio si no existe
if [ ! -d "ponytail" ]; then
    echo -e "${YELLOW}[2/6] Clonando el repositorio de Ponytail...${NC}"
    git clone https://github.com/DietrichGebert/ponytail.git
else
    echo -e "${GREEN}[2/6] El repositorio 'ponytail' ya existe localmente. Saltando clonación.${NC}"
fi

# 3. Crear enlaces simbólicos para el plugin y los comandos
echo -e "${YELLOW}[3/6] Vinculando componentes dentro del proyecto...${NC}"
# Enlace para el plugin .mjs
ln -sf "$(pwd)/ponytail/.opencode/plugins/ponytail.mjs" .opencode/plugins/ponytail.mjs
# Enlaces para todos los comandos
ln -sf "$(pwd)/ponytail/.opencode/command/"* .opencode/command/

# 4. Configurar opencode.json
echo -e "${YELLOW}[4/6] Configurando opencode.json...${NC}"
CONFIG_FILE="opencode.json"
PLUGIN_ENTRY='"./.opencode/plugins/ponytail.mjs"'

if [ ! -f "$CONFIG_FILE" ]; then
    # Crear un opencode.json básico si no existe
    echo -e "{\n  \"plugin\": [\n    $PLUGIN_ENTRY\n  ]\n}" > "$CONFIG_FILE"
    echo -e "${GREEN}Archivo opencode.json creado con la configuración del plugin.${NC}"
else
    # Comprobar si el plugin ya está declarado
    if grep -q "ponytail.mjs" "$CONFIG_FILE"; then
        echo -e "${GREEN}El plugin ya se encuentra configurado en opencode.json.${NC}"
    else
        # Inserción segura usando node para no romper el formato JSON
        node -e "
        const fs = require('fs');
        const file = '$CONFIG_FILE';
        let json = {};
        try { json = JSON.parse(fs.readFileSync(file, 'utf8')); } catch(e) {}
        if (!json.plugin) json.plugin = [];
        if (!json.plugin.includes('./.opencode/plugins/ponytail.mjs')) {
            json.plugin.push('./.opencode/plugins/ponytail.mjs');
        }
        fs.writeFileSync(file, JSON.stringify(json, null, 2));
        "
        echo -e "${GREEN}opencode.json actualizado con éxito.${NC}"
    fi
fi

# 5. Configurar .gitignore para excluir la carpeta clonada y los enlaces generados
echo -e "${YELLOW}[5/6] Configurando .gitignore...${NC}"
GITIGNORE_FILE=".gitignore"

# Definir las reglas que queremos agregar
RULES_TO_ADD=(
    "#"
    "# Ponytail - OpenCode Plugin (Instalación Local)"
    "ponytail/"
    ".opencode/plugins/ponytail.mjs"
    ".opencode/command/*"
)

# Crear .gitignore si no existe
if [ ! -f "$GITIGNORE_FILE" ]; then
    touch "$GITIGNORE_FILE"
fi

# Verificar si ya agregamos ponytail al gitignore para no duplicar lineas
if grep -q "ponytail/" "$GITIGNORE_FILE"; then
    echo -e "${GREEN}Las reglas de Ponytail ya existen en el archivo .gitignore.${NC}"
else
    echo -e "" >> "$GITIGNORE_FILE"
    for rule in "${RULES_TO_ADD[@]}"; do
        echo "$rule" >> "$GITIGNORE_FILE"
    done
    echo -e "${GREEN}Se agregaron las exclusiones de Ponytail a .gitignore.${NC}"
fi

# 6. Finalización
echo -e "${YELLOW}[6/6] Verificando archivos clave...${NC}"
if [ -f "ponytail/AGENTS.md" ]; then
    echo -e "${GREEN}✓ AGENTS.md detectado correctamente.${NC}"
fi

echo -e "\n${GREEN}=== ¡Instalación completada con éxito! ===${NC}"
echo -e "Reinicia tu entorno de OpenCode dentro de esta carpeta para aplicar los cambios."
echo -e "Podrás alternar los modos usando los comandos: ${BLUE}/ponytail lite|full|ultra|off${NC}"