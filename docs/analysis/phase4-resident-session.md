# C115 — integração gráfica residente pronta, teste físico pendente

Preparado em07/11/2026 após C112/C113/C114 aprovados. O usuário se ausentou;
nenhum menu/jogo foi aberto, nenhum botão foi solicitado ou injetado. Este
incremento prepara o comando completo para teste posterior; não é aprovação
física, acústica, de controles ou da restauração neste boot82.

## Integração

O harness mantém supervisor/namespace/worker originais e os limites C109:
menu selecionado por A, jogo até45s, restaurar Fn+L2 e sair Fn+Start. Os dez
scripts C105 continuam preparados no aparelho. Agora `load.sh prepare` C112
fornece os cinco inputs a partir da instalação/p3, antes do C111 original.
A cápsula inicial deve estar vazia. O laço de uploads recebe mapa vazio e não
abre/envia bytes de nenhum asset ou ROM. Marker resident é exigido junto com
C105/C111, run.once, cmdline/PID/starttime e três mapas reais do processo.

As funções antigas de histórico C66/C63 exigiam ROM LOCAL mesmo sem enviá-la.
Um adaptador em memória troca SOMENTE três admissões: existência/tamanho da
fonte local, hash direto da ROM e esse item no loop de hashes de assets.
Cada uma passa a exigir o recibo nativo C113 da ROMp3, com mesmo digest do
C109/C63. Demais hashes/bindings do histórico permanecem originais. O adaptador
usa uma função C66 conferida contra prova congelada e substituição temporária
Python; não escreve/modifica fonte/prova anterior e restaura o binding ao sair.

Um audit hook em run/check recusa open de caminhos /port/roms/. A história
adaptada passou sob essa proibição. O teste de routing executa o laço extraído
com objetos cuja leitura/transporte sempre falham: o laço com mapa vazio não
chamou nenhum deles. Portanto, o arquivo local da ROM deixa de ser dependência
da execução atual, sem inventar ou relaxar o digest esperado. O backup privado
local de C113 e os recibos continuam dependências de auditoria.

## Verificação offline

16casos passaram em `resident-session/checks.v3fz80ec`: origem C112/C113/C114,
boot/UUID/tipos inválidos,191hashes/readiness, história sem ROMlocal, snapshot/
provider e origem observada, recibos ausentes/divergentes, cápsula vazia/marker,
execução do loop sem upload/leitura, load-only/worker/cleanup preservados e
recusa de âncora do histórico alterada. Rede/SSH/GUI/core/reboot são proibidos
nesses checks. Fonte dos quatro assets e do core não foi recompilada.

## Retomada física

Quando o usuário estiver junto do R35S, verificar IP/contador reais. Se ainda
for boot82, nova observação pelo runner pode ser feita sem UI:

```
python3 -B port/scripts/run-phase4-resident-session.py --host 192.168.15.8 --boot 82 --observe
```

Depois usar o stage observe confirmado como `--observation <stage>` para abrir
UMA rodada, confirmar menu ativo e só então pedir A/Start/direcional/Fn+L2/
Fn+Start, sem save/Power/volume/brilho. Se houve novo boot, criar contexto novo
sem reaproveitar UUID82 nem relaxar o vínculo do C112/C113; não reimportar ROM,
reinstalar ou rearmar claims por rotina.

Analisador e fechamento offline próprios reutilizam C77/C109 por âncoras finitas.
Publisher C115 exige análise técnica/física/fechamento da MESMA sessão antes de
criar `dist/phase4/resident-session`. Esse diretório ainda NÃO existe; não gerar
uma confirmação sintética nem publicar prova gráfica de C114 sem UI.

Observação nativa somente leitura já aprovada em `observe.npmqzojq`: boot82,
rootRO,191hashes/payload/fundação e infraestrutura conferidos. Nenhum menu foi
aberto. Pode ser usada na retomada se boot/UUID/estado real e fontes ainda forem
iguais; caso contrário, primeiro reconstruir contexto/observação apropriados.
