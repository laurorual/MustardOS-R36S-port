# C122 — contrato em lote residente

09/11/2026, R35S Panel0, boot84. O objetivo é retirar os seis uploads de código
por sessão, preservando o contrato C120 aprovado fisicamente pelo C121.
O componente novo fica em `/usr/libexec/muos-batch-v1`; C105/C112 e suas provas
não são substituídos. A ativação continua manual, sem autostart ou reboot.

## Pacote e preparação

Nove arquivos,33.699bytes, todos0644, diretório0755: os seis arquivos C120
byte-idênticos, funções de residência, manifesto próprio e entrypoint. Não
há ROM, ELF, seed ou identidade privada. O entrypoint fixa hashes das funções
antes de source; o manifesto próprio fixa as sete folhas de implementação.
O plano/guard200 fixa todas as nove folhas, inclusive manifesto e entrypoint.
Esse padrão preserva a verificação do entrypoint pelo chamador, como nos
componentes C105/C112, sem inventar um hash autorreferente.

`check` confere o pacote, o C105/dependências e readiness/PCM fechado. `adopt`
exige cápsula tmpfs do boot atual já preparada pelo loader C112, role load,
marcadores residentes e todos os scripts/assets originais. Recusa seleção,
run anterior, stage novo ou bundle existente, inclusive dangling symlink.

Um mkdir atômico reserva `contract-v3` antes da primeira folha copiada. As seis
cópias ficam0644 e são comparadas à fonte; só então o caller C120 original faz
a adoção, com sua reserva antiga e seu stage próprios. Cópia parcial/falha de
adoção ficam retidas para inspeção, sem overwrite ou retry. A reserva de run
novo continua ausente; o loader residente não inicia jogo/menu.

A receita opt-in em `port/buildroot-batch` exige payload público explícito,
manifesto de exportação separado e seu digest esperado. Confere nomes, nove
folhas e hashes antes de instalar. Default n; exige base AArch64/session e
C105/C112 já qualificados. Usa ferramentas/SDK existentes, sem dependências
novas no host, compilação de ELF ou imagem integral. O padrão de manifesto
foi consultado no upstream `internal/script/mux/extract.sh`; não houve cópia
ou alteração de referência. Os helpers originais reutilizados são MIT.

## Testes offline

42casos em `resident-batch/checks.3f5yuzvw`, pacote `package.6njmns_6`.
Funções rb/C120 reais em container rootless/offline com fixtures em tmpfs,
source port RO. Cobrem cópia/adopção exata, repetição, manifesto/hash/modo/
links/arquivo estranho, boot/plataforma, role/asset/marker inválidos, cópia
parcial e falha de adoção retidas. A primeira falha foi do harness de transação
por um alias de hash ausente; corrigido antes de planejar/escrever no console.

A transação derivada da fonte congelada C105 usa escopo exato de nove folhas:
instalação/rollback e falhas nos hooks guard/rw/directory/verify/sync/ro e nas
folhas1/5/9. Arquivo vizinho desconhecido bloqueia rollback e é preservado.
A receita real foi executada num target descartável: caso válido e recusas de
input ausente, manifesto incorreto, folha alterada e folha extra. Os checks
não abrem cartão nem ROM; não simulam sucesso físico/GUI.

## Instalação nativa

`resident-batch/install.1a1mvhj9`, mesmo84/IP192.168.15.15. Survey confirmou
prefixo ausente; plano/backup de ausência/deployment regular sincronizados no
host antes da escrita. Uma tentativa, `dispatch.claim` consumido: nove folhas
novas/um diretório, zero substituições. Adapter com trava, guard191/boot/UUID,
private fingerprint e sync/remountRO; check instalado e adoção de cápsula
incompleta recusada sem criar bundle. Rollback fica limitado às folhas
conhecidas e diretórios próprios; não remove vizinhos desconhecidos.

Instalação/check/recusas/fechamento passaram, raizRO e RAM removida; fingerprint
privado, infraestrutura e mountinfo preservados. Não reexecutar apply; preservar
plan/backup/dispatch.claim. Não houve serviço, token, reboot, menu ou save.
O original32 e o Steam Deck não participaram. Imagens/SDK anteriores preservados.

## Validação residente

A validação pós-instalação usa o C112 para preparar uma cápsula nova, chama o
loader residente, compara as seis cópias ao prefixo instalado e ao C120 e
confere staged/recusa de repetição/save/novo run ausente/host check. Ela envia
somente comandos SSH: nenhum input ou arquivo de código do contrato é enviado.
`resident-batch/validate.zxyzyv87`, mesmo84/IP15: dez recibos nativos0.
Guard200 (191anteriores+9novos), preparo C112, adoção pelo loader instalado,
comparação das seis folhas, staged e check do host C120 passaram. Repetição e
modo save recusados, novo run.once ausente. Nenhum arquivo de contrato/input
foi enviado por esse executor; não há leitura da ROM no host.

Infra antes/depois/pós-cleanup e mountinfo global byte-idênticos. Cápsula
removida, raizRO/PCMclosed/UIoff/p1p3off, sem escrita persistente nessa etapa.
Ela lê a ROM interna pelo leitor C112 já qualificado; não executa core, menu,
áudio ou inputs. Os nove arquivos residentes persistem no prefixo instalado.

A prova sanitizada é `dist/phase4/resident-batch-installed`, contendo fontes,
payload público de texto, `export.sha256` para a receita, adaptadores, casos e
resumo; sem privados/ROM/ELF.
Ela não equivale à qualificação gráfica pelo novo loader. O próximo incremento
é vincular o fluxo gráfico ao pacote instalado e confirmar um ciclo load-only,
sem os uploads que o executor C121 ainda faz. Não prometer aceleração de
startup: o ganho desta etapa é residência/proveniência, com guardas completas.
