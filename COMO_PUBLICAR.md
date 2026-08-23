# Como publicar este repositório no GitHub

Este diretório já é um repositório Git com o commit inicial feito. Faltam dois passos.

## 1. Criar o repositório vazio no GitHub

Em <https://github.com/new>:

- **Repository name:** `copa2026-fifa-analytics` (ou o nome que preferir)
- **Public** ou **Private**, à sua escolha
- **Não** marque "Add a README file", "Add .gitignore" nem "Choose a license" —
  esses arquivos já existem aqui e as opções criariam conflito

## 2. Apontar o repositório local para o GitHub e enviar

No terminal, dentro desta pasta (troque `SEU-USUARIO` e o nome do repositório):

```bash
git remote add origin https://github.com/SEU-USUARIO/copa2026-fifa-analytics.git
git push -u origin main
```

Na primeira vez o Git pede autenticação. Duas formas:

- **GitHub CLI** (mais simples, se tiver instalado): `gh auth login` antes do push.
- **Token pessoal:** em Settings → Developer settings → Personal access tokens, gere um token
  com permissão de escrita no repositório e use-o como *senha* quando o Git pedir
  (o usuário é o seu login do GitHub).

Se o seu Git estiver configurado com outro nome de branch padrão, use `git branch -M main`
antes do push.

## 3. Opcional: publicar o dashboard como página

Em **Settings → Pages**, selecione:

- **Source:** Deploy from a branch
- **Branch:** `main` · **Folder:** `/docs`

Em cerca de um minuto o dashboard fica acessível em
`https://SEU-USUARIO.github.io/copa2026-fifa-analytics/`
(a pasta `docs/` contém uma cópia do painel como `index.html`).

Esse link é conveniente para enviar ao professor: abre o dashboard completo no navegador,
sem download.

---

Depois de publicar, este arquivo pode ser apagado — ele serve apenas como guia inicial.
