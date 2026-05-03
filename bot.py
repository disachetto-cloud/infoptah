import feedparser
import schedule
import time
import asyncio
import csv
import os
from datetime import datetime
from telegram import Bot

# ============================================================
# CONFIGURAÇÕES — edite apenas esta seção
# ============================================================

TOKEN = "8345646186:AAFAizarA1y2nISJQ3xSwxt4auysNSQdFYk"        # Token do BotFather
CANAL = "@infoptahbr"             # Username do seu canal

# Feeds RSS — notícias de tech
FEEDS_NOTICIAS = [
    "https://canaltech.com.br/rss/",
    "https://olhardigital.com.br/feed/",
    "https://techtudo.globo.com/rss2.xml",
]

# Feed RSS do seu blog
FEED_BLOG = "https://infoptah.com.br/feed/"

# Arquivo de ofertas (você preenche diariamente)
ARQUIVO_OFERTAS = "ofertas.csv"

# Ativar ou desativar módulos
ATIVAR_NOTICIAS = True
ATIVAR_BLOG     = True
ATIVAR_OFERTAS  = False   # Mude para True quando quiser ativar as ofertas

# Horários de postagem
HORARIO_NOTICIAS_1 = "08:00"
HORARIO_NOTICIAS_2 = "13:00"
HORARIO_NOTICIAS_3 = "19:00"
HORARIO_BLOG       = "09:00"
HORARIO_OFERTAS    = "12:00"

# ============================================================
# CONTROLE DE POSTS JÁ ENVIADOS (evita repetição)
# ============================================================

posts_enviados = set()

def ja_enviado(link):
    return link in posts_enviados

def marcar_enviado(link):
    posts_enviados.add(link)

# ============================================================
# FUNÇÕES DE POSTAGEM
# ============================================================

async def postar_noticias():
    if not ATIVAR_NOTICIAS:
        return

    bot = Bot(token=TOKEN)
    postou = False

    for url_feed in FEEDS_NOTICIAS:
        feed = feedparser.parse(url_feed)
        for entrada in feed.entries[:2]:  # Pega até 2 por feed
            link = entrada.get("link", "")
            if ja_enviado(link):
                continue

            titulo = entrada.get("title", "Sem título")
            resumo = entrada.get("summary", "")[:200].strip()
            fonte  = feed.feed.get("title", "Portal externo")

            mensagem = (
                f"📰 *{titulo}*\n\n"
                f"{resumo}...\n\n"
                f"🔗 [Ler mais]({link})\n"
                f"_Fonte: {fonte}_"
            )

            await bot.send_message(
                chat_id=CANAL,
                text=mensagem,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )

            marcar_enviado(link)
            postou = True
            await asyncio.sleep(3)  # Pausa entre mensagens
            break  # Um por feed por rodada

    if not postou:
        print(f"[{datetime.now()}] Nenhuma notícia nova para postar.")

async def postar_blog():
    if not ATIVAR_BLOG:
        return

    bot = Bot(token=TOKEN)
    feed = feedparser.parse(FEED_BLOG)

    for entrada in feed.entries[:1]:  # Só o post mais recente
        link = entrada.get("link", "")
        if ja_enviado(link):
            print(f"[{datetime.now()}] Post do blog já enviado.")
            return

        titulo = entrada.get("title", "Novo post")
        resumo = entrada.get("summary", "")[:200].strip()

        mensagem = (
            f"✍️ *Novo post no InfoPtah!*\n\n"
            f"*{titulo}*\n\n"
            f"{resumo}...\n\n"
            f"🔗 [Ler no blog]({link})"
        )

        await bot.send_message(
            chat_id=CANAL,
            text=mensagem,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )

        marcar_enviado(link)
        print(f"[{datetime.now()}] Post do blog enviado: {titulo}")

async def postar_ofertas():
    if not ATIVAR_OFERTAS:
        return

    if not os.path.exists(ARQUIVO_OFERTAS):
        print(f"[{datetime.now()}] Arquivo {ARQUIVO_OFERTAS} não encontrado.")
        return

    bot = Bot(token=TOKEN)
    ofertas = []

    with open(ARQUIVO_OFERTAS, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            ofertas.append(linha)

    if not ofertas:
        print(f"[{datetime.now()}] Nenhuma oferta no arquivo.")
        return

    mensagem = "🔥 *Ofertas do dia — Tech*\n\n"
    mensagem += "━━━━━━━━━━━━━━━\n\n"

    emojis = ["🖥️", "📱", "🎧", "⌨️", "🖱️"]

    for i, oferta in enumerate(ofertas[:4]):  # Máximo 4 ofertas por dia
        emoji   = emojis[i % len(emojis)]
        nome    = oferta.get("nome", "Produto")
        preco_de = oferta.get("preco_de", "")
        preco_por = oferta.get("preco_por", "")
        link    = oferta.get("link", "#")

        mensagem += f"{emoji} *{nome}*\n"
        if preco_de:
            mensagem += f"~~R$ {preco_de}~~ → *R$ {preco_por}*\n"
        else:
            mensagem += f"*R$ {preco_por}*\n"
        mensagem += f"🛒 [Ver oferta]({link})\n\n"
        mensagem += "━━━━━━━━━━━━━━━\n\n"

    await bot.send_message(
        chat_id=CANAL,
        text=mensagem,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

    print(f"[{datetime.now()}] Ofertas do dia enviadas.")

# ============================================================
# AGENDADOR
# ============================================================

def rodar_async(coro):
    asyncio.run(coro)

def iniciar_agendamentos():
    schedule.every().day.at(HORARIO_NOTICIAS_1).do(rodar_async, postar_noticias())
    schedule.every().day.at(HORARIO_NOTICIAS_2).do(rodar_async, postar_noticias())
    schedule.every().day.at(HORARIO_NOTICIAS_3).do(rodar_async, postar_noticias())
    schedule.every().day.at(HORARIO_BLOG).do(rodar_async, postar_blog())
    schedule.every().day.at(HORARIO_OFERTAS).do(rodar_async, postar_ofertas())

    print(f"[{datetime.now()}] Bot iniciado! Aguardando horários agendados...")
    print(f"  Notícias: {HORARIO_NOTICIAS_1}, {HORARIO_NOTICIAS_2}, {HORARIO_NOTICIAS_3}")
    print(f"  Blog:     {HORARIO_BLOG}")
    print(f"  Ofertas:  {HORARIO_OFERTAS} (ativo: {ATIVAR_OFERTAS})")

    while True:
        schedule.run_pending()
        time.sleep(30)

# ============================================================
# INÍCIO
# ============================================================

if __name__ == "__main__":
    iniciar_agendamentos()
