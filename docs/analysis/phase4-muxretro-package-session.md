# Fase 4 — C61: host do pacote qualificado em RAM

Em 03/11/2026, o ELF muxretro produzido pela receita C60 foi executado no
R35S em uma sessão GB limitada, com o CLI C57 instalado e backend em leitura.
O usuário confirmou “tudo certo” à pergunta explícita sobre imagem,
direcional, som limpo/audível, restauração Fn+L2 e saída Fn+Start com retorno
ao menu. O host continua somente na bancada; não foi instalado no rootfs.

## Implementação e vínculo das provas

Foram consultados o runner/analisador C59 congelados, o contrato C60 do
pacote, o backend C58 e os scripts de seleção/lifecycle C45/C46/C53. A menor
mudança é um adaptador separado, sem editar os fluxos já aprovados:

- `phase4_muxretro_package_session.py` vincula C59/C60 e os assets;
- `prepare-phase4-muxretro-package-session.py` gera runner/analisador como
  delta exato do C59 congelado, recusando deriva da origem;
- `check-phase4-muxretro-package-session.py` valida recusas e loader;
- `run/analyze/package-phase4-muxretro-package-session.py` executam, analisam
  e congelam a nova prova;
- `muxretro-package-session/stopped-screen.sh` mostra a página final C61.

O runner mantém primeiro os vínculos históricos C53 save/load68 → C54/C58
69 → C59 70 contra o ELF antigo. Depois verifica a prova C60, os treze arquivos
de seu payload e a proveniência, substituindo apenas o host enviado à RAM.
Exige o mesmo contador **e UUID** do C59; se outro boot for encontrado,
recusa antes de alocar a cápsula. Nada afrouxa as guardas antigas para aceitar
um contador ou UUID diferente.

O ELF novo tem SHA256
`8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05`.
O anterior era
`4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd`.
Os checks/ensaios antigos do host são referências históricas, não testes
reutilizados para o ELF novo. Core, ROM privada do usuário, runner, worker,
inspetor de estado, scripts de seleção/store e biblioteca de UI permanecem
os mesmos assets vinculados ao C59. Não houve recompilação nem novo save.

## Escopo da biblioteca frontend e do SDK

O build C60 usa os quatro links privados C38. O preflight nativo confere seus
hashes na fundação instalada. Como no C59, a sessão fornece em RAM a
`libmuxmod.so` C46 da seleção diagnóstica, fixada em
`1ec8acd906ee25bd83b59c0c5818e7310d62bfeaabadb2b473e03562d7d6bcc9`.
Esse override é parte explícita da configuração runtime qualificada.

O novo host passou loader eager A35/QEMU com esse override antes do ensaio.
No próprio R35S, passou `--version` e `--help` com `LD_BIND_NOW=1` e a mesma
ordem de bibliotecas, antes de iniciar serviços/gráficos. Isso complementa o
loader C60 com as bibliotecas de link. C61 não qualifica um frontend completo
sem o override, nem integra o provider de bibliotecas ao Buildroot.

## Checks e ensaio supervisionado

Passaram 52 casos de vínculo/recusa: contador/UUID/identidade/asset divergente,
recibo ou cleanup inválido, pacote sem as verificações exigidas, hash novo
incorreto, tentativa de usar o ELF antigo, fontes/ancestralidade/payload ou
fundação divergente. A geração exata de runner/analisador e a página final
também foram conferidas. Os 34 checks do dispatcher C58 e o lifecycle C45
foram reutilizados para seus bytes inalterados, sem repetir os serviços.

O preflight encontrou C07/boot70/IP192.168.15.14:2222, raiz ext4 RO e mesmo
UUID do C59. O pacote instalado C57 e os quatro links C60 foram conferidos.
A sessão usa a namespace privada/runner limitados já aprovados, p3 em
`ro,noload`, runtime/conteúdo/estado em RAM e CPU/power sysfs protegidos para
leitura. O menu permite até 135 segundos para selecionar; o jogo tem deadline
de 45 segundos, com runner externo de 65 segundos e limite global do worker.

O usuário abriu “R35S-Diagnostic” com A, usou Start/direcional, restaurou o
estado com Fn+L2 e saiu com Fn+Start. Não foi solicitado salvar nem tocar
Power, volume ou brilho. A qualificação visual/acústica depende dessa
confirmação; não é inferida apenas de logs, frames ou ausência de erros.

Recibos: `checks.ds8r19g3` e `load.upr3y148`, sob
`build/phase4/muxretro-package-session/`. O novo host apresentou o primeiro
frame e saiu voluntariamente por hotkey após 1.197 frames, `expired=0`.
Operação e cleanup terminaram em0; retorno ao launcher confirmado nos logs
e fisicamente. A saída interna por deadline do novo ELF não foi exercitada;
o limite externo continua sob responsabilidade do runner inalterado.

O inspetor validou PKST/CRC/manifesto/assinatura PNG e os 26.861 bytes do
core. O CLI instalado realizou dois status e uma exportação para RAM; não
foi enviado outro ELF do store. Geração1/HEAD1/0/2 e inventários do store são
byte-idênticos aos do C59/C58/C54 e antes/depois da sessão. O estado
comercial não foi coletado; as cópias RAM e todos os assets foram removidos.

Fundação97, prefs55/70, mixer, brilho/DRM, volume, WirePlumber, infraestrutura
e mounts globais foram preservados. A conferência final repetiu o contrato
de preflight e encontrou rootRO0755/taint0/PCMclosed, p3 desmontada e nenhuma
UI/serviço temporário ativo. `/opt/muos/frontend/muxretro` continua ausente:
nenhuma instalação do host. Página final C61 enviada após coleta/cleanup.

O CSV registrou quatro callbacks de underrun e 1.932 frames de áudio
ausentes, sem timestamps que localizem a ocorrência. A taxa recente do core
é59,9401Hz e a média registrada de frame16,6833ms; isso não é FPS absoluto ou
medição de toda a sessão. A saída foi voluntária, portanto não dividir
1.197 pelo limite de45s. O som foi confirmado limpo no teste curto; não se
qualifica continuidade acústica nem se atribui causa aos underruns.

## Reprodução e limites

O checker pode ser repetido offline, com os inputs qualificados presentes:

```sh
python3 port/scripts/prepare-phase4-muxretro-package-session.py
python3 port/scripts/check-phase4-muxretro-package-session.py
```

O runner exige IP/boot e recibos explícitos C53 save/load, C54, C58, C59 e
build C60. Não redisparar apenas porque os scripts existem. A coleta local
contém somente logs e metadados selecionados; o snapshot comercial fica no
cartão de teste. O pacote de prova pública exclui ROM, ELF, estado, PNG, INI,
PCM, identidade comercial, hash da ROM e UUID do boot.

Prova congelada em `dist/phase4/muxretro-package-session`, com SHA256SUMS.
As provas C59/C60/C58 e o `.config` compartilhado do SDK foram conferidos
intactos. Cartão original de32GB e Steam Deck não foram acessados; o teste
não pediu reboot nem fez nova gravação de preferências ou save no128GB.

O resultado qualifica este ELF no runtime RAM com o override C46 e o backend
C57/C58 em leitura. Não qualifica inicialização pelo boot, imagem C56/C60,
instalação permanente, perda elétrica, SRAM, GC, Power/suspend, continuidade
acústica ou desempenho de longa duração. Os warnings de build registrados
no C60 e a integração incompleta do provider permanecem questões separadas.

Próximo C62 proposto: preparar um plano de instalação seletiva do host e dos
metadados C60, com inventário/ausência prévia, backup, recuperação e guardas,
mantendo ativação manual. O plano deve tratar explicitamente a dependência
runtime C46; não presumir que instalar só o ELF reproduz o ensaio. Nenhum
writer/autostart ou nova gravação de save faz parte dessa instalação.
