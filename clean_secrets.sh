#!/bin/bash
# ========================================================================
# LIMPIEZA DE SECRETOS EN REPOSITORIO GIT
# ========================================================================
# Este script elimina .env (y otros archivos sensibles) de TODO el historial
# de Git, actualiza .gitignore, crea .env.example y hace push forzado.
#
# USO: 
#   1. Guardar como clean_secrets.sh
#   2. chmod +x clean_secrets.sh
#   3. ./clean_secrets.sh
#
# O bien, copiar y pegar el bloque completo en la terminal (Git Bash)
# dentro del repositorio a limpiar.
# ========================================================================

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   🧹 LIMPIEZA DE SECRETOS - HISTORIAL GIT${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# ========================================================================
# 1. CONFIGURACIÓN INICIAL
# ========================================================================
REPO_PATH="$(pwd)"                     # Directorio actual
BACKUP_DIR="$HOME/Desktop/git_backup_$(date +%Y%m%d_%H%M%S)"
SECRET_FILES=(".env" ".env.local" ".env.backup" "secrets.json" "*.key")
REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null)

echo -e "${GREEN}📁 Repositorio: $REPO_PATH${NC}"
echo -e "${GREEN}💾 Backups temporales en: $BACKUP_DIR${NC}"
mkdir -p "$BACKUP_DIR"

# ========================================================================
# 2. BACKUP DEL .env ACTUAL (si existe)
# ========================================================================
if [ -f ".env" ]; then
    cp ".env" "$BACKUP_DIR/env_backup.txt"
    echo -e "${GREEN}✅ Backup de .env guardado${NC}"
else
    echo -e "${YELLOW}⚠️ No se encontró archivo .env en el working directory${NC}"
fi

# ========================================================================
# 3. INSTALAR/VERIFICAR git-filter-repo
# ========================================================================
if ! command -v git-filter-repo &> /dev/null; then
    echo -e "${YELLOW}📦 Instalando git-filter-repo...${NC}"
    pip install git-filter-repo --quiet
fi

# ========================================================================
# 4. ELIMINAR .env DE TODO EL HISTORIAL
# ========================================================================
echo -e "${BLUE}🌀 Reescribiendo historial para eliminar archivos sensibles...${NC}"
git filter-repo --path .env --path .env.local --path .env.backup --path secrets.json --invert-paths --force

# Después de filter-repo, el remote 'origin' se elimina. Lo guardamos antes.
if [ -n "$REMOTE_URL" ]; then
    echo -e "${GREEN}🔗 Restaurando remote origin: $REMOTE_URL${NC}"
    git remote add origin "$REMOTE_URL"
fi

# ========================================================================
# 5. ACTUALIZAR .gitignore
# ========================================================================
echo -e "${BLUE}📝 Actualizando .gitignore...${NC}"
cat >> .gitignore << 'EOF'

# Secretos y archivos sensibles
.env
.env.local
.env.backup
.env.*.local
secrets.json
*.key
*.pem
EOF

# ========================================================================
# 6. CREAR .env.example (plantilla sin secretos)
# ========================================================================
if [ ! -f ".env.example" ]; then
    echo -e "${BLUE}📄 Creando .env.example...${NC}"
    cat > .env.example << 'EOF'
# === CONFIGURACIÓN REQUERIDA ===
# Copia este archivo a .env y completa tus claves

# API Keys
OPENAI_API_KEY=sk-your-key-here
OPENROUTER_API_KEY=sk-or-v1-your-key

# Supabase (si aplica)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Email (IONOS u otro)
SMTP_SERVER=smtp.ionos.es
SMTP_PORT=587
SMTP_USER=your-email@ingecart.es
SMTP_PASSWORD=your-password

# Base de datos (si aplica)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
EOF
fi

# ========================================================================
# 7. COMMIT DE LOS CAMBIOS DE SEGURIDAD
# ========================================================================
git add .gitignore .env.example
git commit -m "chore(security): add .gitignore and .env.example (secrets removed from history)"

# ========================================================================
# 8. PUSH FORZADO (con manejo de errores de protección de GitHub)
# ========================================================================
echo -e "${BLUE}🚀 Intentando push forzado...${NC}"
if git push origin main --force; then
    echo -e "${GREEN}✅ Push completado exitosamente${NC}"
else
    echo -e "${RED}❌ Push bloqueado por GitHub Push Protection${NC}"
    echo -e "${YELLOW}🔗 Para desbloquear, abre los siguientes enlaces en tu navegador (uno por cada secreto detectado):${NC}"
    echo -e "${YELLOW}   Se mostrarán en el mensaje de error anterior. También puedes ir a:${NC}"
    echo -e "${BLUE}   https://github.com/senarzuniga/REPO_NAME/security/secret-scanning${NC}"
    echo -e "${YELLOW}   Luego haz clic en 'Unblock secret' para cada secreto.${NC}"
    echo -e "${YELLOW}   Una vez desbloqueados, vuelve a ejecutar: git push origin main --force${NC}"
fi

# ========================================================================
# 9. RESUMEN FINAL
# ========================================================================
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ PROCESO COMPLETADO${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📌 IMPORTANTE:${NC}"
echo -e "   1. El historial local ya NO contiene los secretos."
echo -e "   2. Si el push fue bloqueado, sigue las instrucciones de desbloqueo."
echo -e "   3. Una vez subido el historial limpio, ROTA (cambia) tus claves en:"
echo -e "      - OpenAI: https://platform.openai.com/api-keys"
echo -e "      - Supabase: https://app.supabase.com/project/_/settings/api"
echo -e "      - OpenRouter: https://openrouter.ai/keys"
echo -e "   4. Restaura tu .env local con las NUEVAS claves:"
echo -e "      cp $BACKUP_DIR/env_backup.txt .env (luego edita y reemplaza claves)"
echo ""
echo -e "${BLUE}💾 Backup de tus claves antiguas (SOLO PARA REFERENCIA):${NC}"
echo -e "   $BACKUP_DIR/env_backup.txt"
echo ""