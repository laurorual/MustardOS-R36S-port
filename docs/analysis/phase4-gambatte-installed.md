# C76 — instalação seletiva do core Gambatte

Concluído em03/11/2026, no cartão de teste128GB/R35S/boot72/IP192.168.15.18.
O core C75 foi instalado em `/opt/muos/share/core/gambatte_libretro.so`,0644,
SHA256 `3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57`.
É byte a byte o core já utilizado no C73. Nenhum jogo foi repetido.

Foram acrescentados nove arquivos e oito diretórios, sem substituir arquivos
existentes: core, revisão de licenças, seis avisos/fontes com licença e o
manifesto. O survey novo confirmou ausência das três raízes do pacote e seus
temporários, pais root0755 sem symlinks e os132pré-requisitos preexistentes:
fundação97, store4 e host/provider31. Kernel/modelo/mídia128/raizRO/boot/UUID,
PCM fechado, UI/p3off, taint0 e rede passaram nas guardas do ponto de aplicação.
O cartão original32 e o Steam Deck não foram acessados.

O [preparador](../../port/scripts/prepare-phase4-gambatte-install.py) deriva
uma política própria da transação C62 congelada. Fixa as nove folhas0644,
oito diretórios e três raízes, incluindo proteção dos vizinhos sob core.
Não amplia ou modifica a antiga política do host. O [executor](../../port/scripts/run-phase4-gambatte-install.py)
usa boot/UUID exatos para aplicação e recuperação, lifetime lock, fingerprint
privado, publicação exclusiva por folha e trap para rollback/retorno RO.
O diretório compartilhado de lock em RAM é validado/preparado como no C74.

O backup é de ausência: zero arquivos originais precisavam ser copiados.
Plano, ausência registrada e implantação foram fsynced no host antes de RW.
Stage independente de recuperação:
`build/phase4/gambatte-install/install.ucdyhb4b`.
Rollback retira somente folhas com bytes/modos reconhecidos e diretórios
vazios registrados no journal. Conteúdo inesperado ou vizinhos são preservados.
Não restaurar backups antigos de seed, contador, keys ou saves para recuperar
este pacote. A recuperação após outro boot exige novo vínculo explícito;
o executor atual não afrouxa a guarda do boot72. Rollback/perda elétrica não
foram exercidos no cartão.

Passaram [50fixtures](../../port/scripts/check-phase4-gambatte-install.py)
em filesystem sintético: aplicação/rollback completos, falha em cada uma das
8criações,9staging e9publicações, guarda/fundação/mode/hash/caminho/colisões/
symlinks e retorno RO. Verificam preservação de vizinhos, inclusive folha e
diretório vazio dentro da nova raiz core. O percurso dirname BusyBox/A35 com
`//` também passou. Nenhum core ou ROM executado nas fixtures; remounts reais
sob falha não foram qualificados por esses testes.

Inspect/apply0, nove folhas regulares root/link1/modo0644 e oito diretórios
root0755 conferidos. Manifesto do pacote e132pré-requisitos válidos. Um probe
MIT foi recompilado de fontes e header fixados, transferido à RAM e executado
com resolução eager contra o core instalado. Confirmou libretro API1,
identidade Gambatte e suporte a conteúdo em memória; não chama retro_init,
não carrega ROM nem inicializa vídeo/áudio/input do jogo.

RaizRO0755/PCMclosed/p3off/UIoff/taint0, fingerprint privado e infraestrutura
PID/starttime preservados. Mounts globais idênticos; cápsula RAM retirada e
saúde final conferida novamente. Nenhum caller/serviço/token/autostart/reboot
foi habilitado, nem nova imagem gravada. A tela permanece no diagnóstico C07.
SDK, host/provider instalados e store/snapshot anteriores permanecem intactos.

A prova `dist/phase4/gambatte-installed` contém somente fontes do port, plano,
backup de ausência e recibos sanitizados. Exclui ELF, tar, UUID e estado privado.
A revisão conjunta GPLv2/GPLv3/MIT continua pendente, registrada no próprio
pacote; esta instalação privada não aprova sua redistribuição.

Próximo recorte: adaptar o dispatcher e o vínculo de sessão para exigir as nove
folhas instaladas e usar esse core pelo caminho fixo, sem copiar outro core
para a cápsula. Validar os novos caminhos e mapas antes da conferência física.
O jogo C73 já aprovado não deve ser repetido por rotina; a futura sessão deve
qualificar especificamente o caller instalado. Autostart permanente, boot de
imagem, Power/suspend, SRAM e resistência a perda elétrica continuam separados.
