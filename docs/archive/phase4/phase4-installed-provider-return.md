# C74 — pacote instalado após reboot do usuário

Concluído em03/11/2026, IP192.168.15.18/boot72. O usuário informou que reiniciou
o aparelho. O UUID atual é diferente do71; nenhum reboot foi solicitado pelo
agente. A sessão C73 continua qualificada no71 e foi fechada pelos recibos
autênticos já coletados, sem executá-la novamente ou afrouxar sua guarda.

O [checker](../../port/scripts/check-phase4-installed-provider-return.py)
usa um vínculo próprio: boot observado72, UUID novo e estado C72 instalado.
Conferiu31folhas/root/modos/link1,29diretórios novos, ausência dos13 antigos,
101pré-requisitos, fundação97 e C25/C07 quieto. Dlopen eager dos4 providers
instalados e muxretro version/help passaram sob o lifetime lock. Não inicializa
core, ROM, UI, áudio, store ou sessão; não escreve arquivos persistentes.

A primeira checagem encontrou `/run/muos/session` ausente neste boot limpo,
antes de executar qualquer probe. A retomada prepara esse diretório em RAM
com modo700 e valida owner/tipo antes do lock, seguindo o runner existente.
O erro original está preservado; a mesma cápsula foi reutilizada e retirada
após sucesso. Isso corrige a preparação deste ensaio, não altera o init ou
qualifica um serviço novo. Fonte anterior retida no stage para comparação.

Stage: `build/phase4/installed-provider-return/check.hx6lzi03`.
RaizRO, PCM fechado, p3off, taint0, infraestrutura PID/starttime e mounts
globais preservados, zero assinaturas selecionadas de erro de kernel/storage.
RAM removida; SDK intacto. Prova pública só fontes e recibos sanitizados.

O usuário confirmou que o texto piscando no rodapé desapareceu após reboot.
A leitura atual informa fbcon cursor_blink=1 e vt.global_cursor_default=0;
isso não demonstra a causa do texto anterior. Não foi feito novo teste gráfico
nem alteração de cursor, framebuffer ou printk. Registrar como observação
transitória a investigar se reaparecer, sem declarar correção.

Original32 e Steam Deck preservados. C70 continua imagem privada não bootada;
autostart permanente, Power/suspend e resistência a perda elétrica separados.
