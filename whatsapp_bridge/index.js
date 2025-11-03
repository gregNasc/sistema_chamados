// index.js
import express from 'express';
import { create, Whatsapp } from 'venom-bot';
import bodyParser from 'body-parser';
import cors from 'cors';
import fetch from 'node-fetch';

const app = express();
app.use(cors());
app.use(bodyParser.json());

let clientVenom = null;

const VENOM_OPTIONS = {
  session: 'sistema_chamados',
  multidevice: true,
  disableWelcome: true,
  // Mostre navegador para debug se precisar
  puppeteerOptions: {
    headless: false, // trocar para false se quiser ver o navegador
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--disable-gpu',
      '--window-size=1200,800'
    ]
  }
};

// util: aguarda n ms
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function waitForWapiReady(client, timeout = 20000) {
  // tenta até timeout verificar se WAPI está disponível
  const interval = 1000;
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    try {
      // usa evaluate no contexto para verificar existência do WAPI e do método
      const res = await client.browser.page.evaluate(() => {
        // se window.WAPI e função esperada existirem, retornamos true
        return !!(window && window.WAPI && (typeof window.WAPI.getMaybeMeUser === 'function' || typeof window.WAPI.getMeUser === 'function'));
      }).catch(() => false);
      if (res) return true;
    } catch (err) {
      // ignora e tenta novamente
    }
    await sleep(interval);
  }
  return false;
}

create(VENOM_OPTIONS).then(async (client) => {
  clientVenom = client;
  console.log('✅ Venom iniciado e conectado!');

  // opcional: monitorar estado
  client.onStateChange((state) => {
    console.log('📶 Venom state:', state);
  });

  // onMessage já existente
  client.onMessage(async (message) => {
    if (message.body && !message.isGroupMsg) {
      console.log('📥 Mensagem recebida de', message.from, ':', message.body);

      // encaminhar para Django (ajuste URL conforme seu backend)
      try {
        await fetch('http://127.0.0.1:8000/api/chat/whatsapp/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            numero: message.from,
            texto: message.body
          })
        });
      } catch (err) {
        console.error('Erro ao enviar mensagem ao Django:', err);
      }
    }
  });

}).catch(err => {
  console.error('Erro ao iniciar Venom:', err);
});

// função de envio robusta com retries
async function safeSendText(numero, texto, attempts = 3) {
  if (!clientVenom) throw new Error('clientVenom não iniciado');

  // checar conexão
  const isConnected = await clientVenom.isConnected();
  if (!isConnected) {
    throw new Error('Venom não está conectado');
  }

  // garantir que WAPI esteja pronto
  const ok = await waitForWapiReady(clientVenom, 15000);
  if (!ok) {
    console.warn('WAPI não respondeu a tempo — tentando enviar mesmo assim (pode falhar)');
  }

  let lastErr = null;
  for (let i = 0; i < attempts; i++) {
    try {
      // venom aceita números com sufixo @c.us
      const target = numero.includes('@') ? numero : `${numero}@c.us`;
      const res = await clientVenom.sendText(target, texto);
      return res;
    } catch (err) {
      lastErr = err;
      console.warn(`Tentativa ${i+1} falhou ao enviar para ${numero}: ${err && err.message ? err.message : err}`);
      await sleep(1000 * (i+1)); // backoff simples
    }
  }
  throw lastErr;
}

// endpoint HTTP que o Django pode chamar
app.post('/send', async (req, res) => {
  const { numero, texto } = req.body || {};
  if (!numero || !texto) return res.status(400).json({ error: 'numero e texto obrigatorios' });
  try {
    const result = await safeSendText(numero, texto);
    return res.json({ status: 'ok', result });
  } catch (err) {
    console.error('Erro ao enviar via Venom:', err);
    return res.status(500).json({ error: String(err) });
  }
});

app.listen(3333, () => console.log('🚀 API Venom rodando na porta 3333'));
