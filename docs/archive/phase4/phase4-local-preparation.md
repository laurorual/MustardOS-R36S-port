# C107–C108 — preparação local da cápsula

Data: 07/11/2026. Parte de uma rodada agrupada: preparar, instalar e integrar
antes de pedir um único teste físico do fluxo completo. Scripts originais MIT.

## C107: preparação e contrato

O pacote contém seis arquivos 0644 em `/usr/libexec/muos-capsule`, com apenas
10.542 bytes: funções, manifestos/contrato/licença e entrada `prepare.sh`.
Não contém ROM, ELF, estado, seed ou identidade privada e não modifica C105.

O host fornece somente cinco arquivos em uma cápsula tmpfs 0700 própria:
runner, state-metadata, libmuxmod diagnóstico C46, probe ABI e a ROM privada.
Quatro são assets públicos fixados por hash; a ROM continua somente em RAM.
As outras sete cópias de bibliotecas vêm da instalação já qualificada.
Não há montagem nova de p3 nem cópia da ROM para armazenamento persistente.

`prepare.sh prepare <capsule>` valida pacote/mídia/C07, entradas, pais,
modos/links/hashes e core instalado antes de iniciar um stage. Exige que só
exista o diretório inputs com os cinco arquivos. Colisão, alias, input extra,
core divergente ou tamanho inadequado de ROM são recusados. Uma tentativa
parcial fica marcada e não pode ser repetida ou sobrescrita silenciosamente.

O stage C105 original fornece os dez scripts e o vínculo ao boot. O novo
preparador cria os diretórios, copia os 11 assets públicos e a ROM, produz os
metadados e calcula a identidade SHA256 do snapshot a partir do core/ROM.
Os bytes binários dos dois hashes são enviados por pipe, incluindo o NUL do
prefixo contratual, sem armazenar NUL em variáveis shell. A identidade e o
manifesto são conferidos contra uma implementação Python independente.
Somente role=load é emitido; no fechamento reutiliza c105_staged/c105_assets.

**42 casos locais passaram** em `capsule-prepare/checks.rf47e8wv`: preparo
completo com funções C105 reais, identidade/manifesto, tamper/modos/aliases/
hardlink/neighbors, ROM/core/biblioteca incorretos, falhas platform/tmpfs/
stage/final, cópias parciais 1/7/11/12 e repetição. Também exercitam a transação
real do novo escopo de seis folhas com rollback e falhas 1/3/6. As chamadas de
mídia são mockadas; não executam ROM, core, namespace ou acesso de rede.

## C108: instalação

Instalação concluída no boot 81, em `capsule-prepare/install.0ebv0j0g`.
O adaptador deriva do C105 congelado: prefixo e seis folhas próprios, ausência
anterior, 160 arquivos do contexto C106 conferidos, nenhuma substituição e
uma única aplicação. O fingerprint privado, a infraestrutura e as montagens
globais permaneceram iguais. A raiz voltou a RO e a cápsula RAM foi removida.

O preparador instalado passou em `check` sem abrir interface. Também recusou
uma cápsula vazia sem qualquer mutação. Todos os recibos nativos e o
pós-fechamento terminaram em zero. Nenhum autostart, reboot, jogo ou save foi
executado nesta etapa; a integração gráfica fica para C109.

## Limites e próximo fluxo

C109 usará esse preparador instalado antes de `caller.sh run`. A conferência
física fica para o fim dessa integração; até lá não se afirma aprovação
gráfica do preparador. Ainda existem quatro assets públicos fornecidos pelo
host e uma ROM RAM; preparar tudo a partir de uma biblioteca persistente exige
planejamento separado de licenças/origem da ROM e leitura do volume de dados.
