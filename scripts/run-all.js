#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');
const os = require('os');
const http = require('http');

const isWindows = os.platform() === 'win32';
const rootDir = path.dirname(__dirname);

console.log('\n========================================');
console.log('  AJAX Super-Agent - Local Setup');
console.log('========================================\n');

const processes = [];

// Check if Ollama is already running
function checkOllamaRunning() {
  return new Promise((resolve) => {
    const req = http.get('http://localhost:11434', { timeout: 1000 }, (res) => {
      resolve(true);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

// Helper function to spawn process
function spawnProcess(name, cmd, args, cwd, ignoreErrors = false) {
  console.log(`Iniciando ${name}...`);
  const proc = spawn(cmd, args, {
    cwd: cwd || rootDir,
    stdio: 'inherit',
    shell: isWindows,
  });

  proc.on('error', (err) => {
    if (!ignoreErrors) {
      console.error(`❌ Erro ao iniciar ${name}:`, err.message);
    }
  });

  processes.push(proc);
  return proc;
}

async function main() {
  console.log('Verificando se Ollama já está rodando...\n');

  const ollamaRunning = await checkOllamaRunning();

  if (ollamaRunning) {
    console.log('✅ Ollama já está rodando na porta 11434\n');
  } else {
    console.log('Iniciando Ollama (pode levar alguns segundos)...\n');
    spawnProcess('Ollama', isWindows ? 'ollama' : 'ollama', ['serve'], null, true);
  }

  // Pull qwen2.5-coder:1.5b if not present
  console.log('Verificando modelo qwen2.5-coder:1.5b...\n');
  try {
    const pullReq = http.request({
      hostname: 'localhost',
      port: 11434,
      path: '/api/tags',
      method: 'GET',
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const models = JSON.parse(data).models || [];
          const hasModel = models.some(m => (m.name || m.model || '').includes('qwen2.5-coder:1.5b'));
          if (!hasModel) {
            console.log('📥 Baixando qwen2.5-coder:1.5b (primeira vez, ~986MB)...\n');
            const pull = spawn(isWindows ? 'ollama' : 'ollama', ['pull', 'qwen2.5-coder:1.5b'], { stdio: 'inherit', shell: isWindows });
            pull.on('exit', (code) => {
              if (code === 0) {
                console.log('✅ Modelo qwen2.5-coder:1.5b pronto!\n');
              } else {
                console.log('⚠️ Falha ao baixar modelo. Você pode rodar manualmente: ollama pull qwen2.5-coder:1.5b\n');
              }
            });
          } else {
            console.log('✅ Modelo qwen2.5-coder:1.5b já instalado\n');
          }
        } catch (e) {
          console.log('⚠️ Não foi possível verificar modelos.\n');
        }
      });
    });
    pullReq.on('error', () => console.log('⚠️ Ollama não respondeu ainda para verificar modelos.\n'));
    pullReq.end();
  } catch (e) {
    console.log('⚠️ Erro ao verificar modelo.\n');
  }

  // Wait 2 seconds before starting backend
  setTimeout(() => {
    const pythonCmd = isWindows
      ? path.join(rootDir, 'app/backend/venv_backend/Scripts/python.exe')
      : 'python';
    spawnProcess('Backend', pythonCmd, ['-m', 'uvicorn', 'server:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], path.join(rootDir, 'app/backend'));
  }, 2000);

  // Wait 4 seconds before starting frontend
  setTimeout(() => {
    spawnProcess('Frontend', 'yarn', ['start'], path.join(rootDir, 'app/frontend'));
  }, 4000);

  setTimeout(() => {
    console.log('\n✅ Todos os processos iniciados!');
    console.log('   Backend: http://localhost:8000');
    console.log('   Frontend: http://localhost:3000');
    console.log('   Docs: http://localhost:8000/docs\n');
    console.log('Pressione Ctrl+C para encerrar\n');
  }, 5000);
}

main();

// Cleanup on exit
process.on('SIGINT', () => {
  console.log('\n\nEncerrando processos...');
  processes.forEach(proc => {
    try {
      proc.kill();
    } catch (e) {
      // ignore
    }
  });
  setTimeout(() => process.exit(0), 500);
});

