[![CI](https://github.com/Diogo-Damasceno/github-autobot/actions/workflows/ci.yml/badge.svg)](https://github.com/Diogo-Damasceno/github-autobot/actions)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

# github-autobot

Bot leve que **melhora a si mesmo diariamente** e faz commits automáticos no GitHub.

- Repositório **único** (seguro): o bot só altera este próprio repositório.
- Tarefas **idempotentes**: rodar de novo não duplica trabalho.
- Tudo **verificado** antes de commitar (syntax check / pytest / YAML).
- Zero dependências (apenas Python stdlib).
- Agendado via **systemd user timer** (roda em segundo plano, silencioso).

## O que ele faz por dia

1. Escolhe a próxima melhoria pendente (CI, lint, badges, testes, docs).
2. Aplica (se ainda não aplicada) e verifica.
3. Escreve uma linha no `CHANGELOG.md`.
4. Faz commit (e push, se houver remote) — identidade do dono, sem menção a IA.

## Uso

```bash
python -m github_autobot            # 1 rodada (commit diário)
python -m github_autobot --dry      # simula, não commita
python -m github_autobot --install  # instala systemd user timer (diário)
```

## Agendamento (Arch + Hyprland)

```bash
python -m github_autobot --install
systemctl --user enable --now github-autobot.timer
systemctl --user list-timers | grep autobot
```

> ⚠️ Ferramenta de automação pessoal. Use apenas no seu próprio repositório.
