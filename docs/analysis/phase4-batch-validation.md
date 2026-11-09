# C118 — verificações por lote, protótipo check-only

09/11/2026, R35S Panel0, boot83. C117 mediu cerca de3s por verificação completa
do host e0,61s do provider isolado. C118 implementa um protótipo POSIX shell
que agrupa as consultas e hashes, sem retirar validações nem modificar os
scripts C105/C77 instalados. Não compila ELF, gera imagem ou usa o Steam Deck.

## Implementação e contratos

O gerador confere as fontes MIT `installed-host.sh` e `frontend-libs.sh` contra
a prova C116 e extrai os manifestos exatos40/7. Substitui somente seus loops de
verificação por um `stat` de todos os caminhos e um `sha256sum -c` do manifesto.
Consulta também cada ancestral do host, uma vez por chamada. Não há cache
persistente de confiança ou omissão de checks em chamadas posteriores.

`stat` sem dereference fornece uid/gid/modo/nlink/tipo raw `%f` e caminho. O
resultado completo deve coincidir com o modelo esperado, inclusive quantidade
e ordem. Tipo regular/diretório é conferido pelos bits raw; arquivos vazios
continuam válidos quando o digest corresponde. Nlink de folhas deve ser1;
nlink de diretórios não era pinado no original e continua não pinado. Donos,
grupos, modos especiais, symlinks e ancestrais inválidos são recusados antes
de ler conteúdo. Falha/saída incompleta do stat ou divergência do SHA não é
convertida em sucesso. Os guards de raizRO/tmpfs/cápsula/role/dependências
continuam fora do bloco e intactos.

Os scripts upstream `internal/script/mux/extract.sh` e provisão nxengine usam
manifestos com sha256sum; C118 usa a mesma ferramenta do sistema. Não copia
esses scripts. Os adaptadores do port reutilizados são MIT. Nenhuma referência
upstream foi alterada.

Dois programas gerados, host19836bytes/provider2406bytes, entram somente na RAM,
com modo700, hashes idênticos aos testados e conferência após a comparação.
Isso são dois uploads de código de teste; ROM/ELFs/assets continuam residentes,
sem upload nem open da ROM local. A operação launch é explicitamente recusada
nesta versão. Os scripts originais são conferidos antes/depois.

## Testes locais

51casos `batch-validation/checks.y3mlvyey` passaram, dos quais36 com stat/SHA
reais em container rootless, offline, rootfs/portRO e fixtures em tmpfs.
CAP_CHOWN somente no namespace permite variar dono/grupo das fixtures; não
altera usuários ou permissões do host. Há paridade de aceitação/recusa entre
loop antigo e lote para digest, ausência, modo/especial, dono/grupo, hardlink,
symlink/dangling, diretório no lugar da folha, FIFO, ancestrais e nlink não
pinado de diretórios. FIFO é recusado antes do hash, sem bloqueio.

Uma transformação inversa reconstrói exatamente as fontes originais fora das
mudanças declaradas (bloco, recusa launch, marker e dependência do provider).
Há testes de modelo/path inválido, CLI launch recusada, shell parsing, eventos
de medição incompletos/desordenados e witnesses ausentes. Os testes não acessam
o console nem abrem ROM. Falhas iniciais do próprio laboratório — contagem
incluindo o header preservado, cleanup de dono alterado e hardlink entre dois
tmpfs — foram corrigidas antes de iniciar qualquer ensaio no aparelho.

## Ensaio nativo

Comparação automática check-only, sem UI/core/botões/áudio. Três repetições,
ordem alternada entre original e lote, relógio `/proc/uptime` centesimal,
caches aquecidos/overhead incluído e frequência não controlada. O host inclui
a verificação do provider; as linhas isoladas não devem ser somadas ao host.
Mede verificações, não a abertura real de um jogo ou o tempo físico do botão.

`batch-validation/profile.k9alzk15`,12recibos nativos0, análise passada:

| Verificação | Amostras em ms | Mediana |
| --- | --- | --- |
| Host original, inclui provider | 2980 /3010 /2990 | 2990ms |
| Host em lote, inclui provider em lote | 1150 /1120 /1130 | 1130ms |
| Provider original isolado | 600 /600 /600 | 600ms |
| Provider em lote isolado | 560 /560 /560 | 560ms |

Redução da mediana do check completo:62,2% nesta comparação (1860ms por chamada).
O provider isolado teve ganho pequeno,40ms, e não deve ser apresentado como
grande melhoria. Não somar o provider ao host, que já o chama. Não estimar ganho
real da abertura como duas vezes1860ms: launch e ciclo gráfico não foram medidos.

Guard191/rootRO,11assets/10scripts/metadados originais, bytecode dos protótipos
(scripts/hash/modo/link) antes/depois, run.once ausente e12witnesses de check
conferidos. Infra antes/depois/pós-cleanup e mountinfo global byte-idênticos.
Cápsula removida, PCMclosed/UIoff/p1p3off/raizRO0755; nenhuma escrita persistente,
save, reboot ou mudança no cartão original32. Arquivos instalados intactos.
Não houve código compilado; ABI/SDK/providers/core não mudaram.

Prova sanitizada `dist/phase4/batch-validation`: resumo/métricas/checks/fontes,
sem ROM/ELFs/UUID/identidade privada/seed/estado. C118 não amplia a aprovação
gráfica/acústica C116 nem qualifica launch ou nova imagem de firmware.

## Integração posterior

Mesmo com ganho no benchmark, C118 não acelera ainda a abertura do launcher:
os componentes instalados continuam executando os scripts anteriores. O caller
C105 fixa os hashes do conjunto preparado; substituição avulsa invalidaria
esse contrato e provas históricas. Próximo passo é uma versão explícita do
contrato/preparador, preservando o caminho anterior, antes de qualificar o
fluxo gráfico com launch habilitado e os mesmos checks de conteúdo/estado.
