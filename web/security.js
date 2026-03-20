/**
 * security.js — Shield de Segurança em Runtime (Client-side)
 * Structure Builder Pro | Segurança v1.0
 *
 * Protege:
 *   SEC-003 — Injeção em atributos onclick inline (paths no window.*)
 *   SEC-005 — mermaid.initialize com securityLevel: 'loose'
 *   SEC-009 — Poluição do escopo global window
 *   SEC-001 — Defesa em profundidade para XSS via innerHTML
 *
 * Carregado pelo shield2.py antes de qualquer outro script da aplicação.
 * Executa em IIFE para não poluir o escopo global.
 */

(function (global) {
    'use strict';

    var LOG = '[SECURITY]';

    // ═══════════════════════════════════════════════════════════════════════
    // 1. PATCH DE innerHTML — Defesa em Profundidade (SEC-001)
    //
    // Intercepta toda atribuição de innerHTML e neutraliza padrões de ataque
    // conhecidos sem interferir nos onclick legítimos da aplicação
    // (togglePasta, toggleMirrorNode, etc.).
    // ═══════════════════════════════════════════════════════════════════════

    (function instalarPatchInnerHTML() {
        var desc = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
        if (!desc || !desc.set) return;

        // Padrões que nunca devem aparecer em dados legítimos da aplicação
        var PADROES_MALICIOSOS = [
            /<script\b/i,
            /\bjavascript\s*:/i,
            /<iframe\b/i,
            /\bdata\s*:\s*text\/html/i,
        ];

        Object.defineProperty(Element.prototype, 'innerHTML', {
            set: function (valor) {
                if (typeof valor === 'string') {
                    var detectado = false;
                    for (var i = 0; i < PADROES_MALICIOSOS.length; i++) {
                        if (PADROES_MALICIOSOS[i].test(valor)) {
                            detectado = true;
                            break;
                        }
                    }
                    if (detectado) {
                        console.warn(LOG, 'innerHTML: padrão malicioso detectado e neutralizado.');
                        valor = valor
                            .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                            .replace(/\bjavascript\s*:/gi, 'blocked:')
                            .replace(/<iframe\b[^>]*>[\s\S]*?<\/iframe>/gi, '');
                    }
                }
                desc.set.call(this, valor);
            },
            get: desc.get,
            configurable: true,
            enumerable: true
        });

        console.log(LOG, 'Patch innerHTML instalado.');
    })();


    // ═══════════════════════════════════════════════════════════════════════
    // 2. PROTEÇÃO DE GLOBAIS window — Trap de Propriedade (SEC-003 / SEC-009)
    //
    // Intercepta o momento exato em que script.js atribui as funções
    // window.confirmarRestauracaoMemory e window.deletarMemory,
    // envolvendo-as com validação antes de armazená-las.
    //
    // Técnica: Object.defineProperty com setter na propriedade do window.
    // Isso funciona porque security.js carrega ANTES de script.js.
    // ═══════════════════════════════════════════════════════════════════════

    (function instalarTrapsGlobais() {

        function validarPathMemory(path) {
            if (typeof path !== 'string' || path.length === 0 || path.length > 512) {
                return false;
            }
            // Bloqueia null bytes e quebras de linha
            if (/[\x00\x0d\x0a]/.test(path)) {
                return false;
            }
            // O path deve ser uma chave conhecida em mirroringState.pinnedSnapshots
            // (mirroringState é definido em script.js — acessível pelo escopo global compartilhado)
            try {
                if (
                    typeof mirroringState !== 'undefined' &&
                    mirroringState.pinnedSnapshots !== null &&
                    typeof mirroringState.pinnedSnapshots === 'object'
                ) {
                    if (!Object.prototype.hasOwnProperty.call(mirroringState.pinnedSnapshots, path)) {
                        console.warn(LOG, 'Path de memória não reconhecido bloqueado:', path.substring(0, 80));
                        return false;
                    }
                }
            } catch (e) {
                // mirroringState ainda não inicializado — permite (script.js ainda não rodou)
            }
            return true;
        }

        function criarWrapperConfirmar(fn) {
            return function confirmarRestauracaoMemory_seguro(path) {
                if (!validarPathMemory(path)) return;
                return fn(path);
            };
        }

        function criarWrapperDeletar(fn) {
            return async function deletarMemory_seguro(path) {
                if (!validarPathMemory(path)) return;
                return await fn(path);
            };
        }

        // Instala trap para confirmarRestauracaoMemory
        var _confirmar = undefined;
        Object.defineProperty(global, 'confirmarRestauracaoMemory', {
            get: function () { return _confirmar; },
            set: function (fn) {
                _confirmar = (typeof fn === 'function') ? criarWrapperConfirmar(fn) : fn;
                console.log(LOG, 'window.confirmarRestauracaoMemory protegida.');
            },
            configurable: true,
            enumerable: true
        });

        // Instala trap para deletarMemory
        var _deletar = undefined;
        Object.defineProperty(global, 'deletarMemory', {
            get: function () { return _deletar; },
            set: function (fn) {
                _deletar = (typeof fn === 'function') ? criarWrapperDeletar(fn) : fn;
                console.log(LOG, 'window.deletarMemory protegida.');
            },
            configurable: true,
            enumerable: true
        });

        console.log(LOG, 'Traps de propriedade window instaladas (confirmarRestauracaoMemory, deletarMemory).');
    })();


    // ═══════════════════════════════════════════════════════════════════════
    // 3. PATCH DO MERMAID — Bloqueio de securityLevel: 'loose' (SEC-005)
    //
    // Intercepta mermaid.initialize() e força securityLevel: 'antiscript',
    // impedindo a renderização de HTML/JS arbitrário nos diagramas.
    // Usa polling leve porque o Mermaid carrega de CDN após o DOM.
    // ═══════════════════════════════════════════════════════════════════════

    (function instalarPatchMermaid() {
        var TENTATIVAS_MAX = 100; // 5 segundos (50ms × 100)
        var tentativas = 0;

        function tentar() {
            tentativas++;

            if (typeof global.mermaid === 'undefined') {
                if (tentativas < TENTATIVAS_MAX) {
                    setTimeout(tentar, 50);
                } else {
                    console.warn(LOG, 'Mermaid não detectado após 5s — patch não aplicado.');
                }
                return;
            }

            if (typeof global.mermaid.initialize !== 'function') return;

            // Evita duplo-patch
            if (global.mermaid.initialize._shielded) return;

            var originalInit = global.mermaid.initialize.bind(global.mermaid);

            global.mermaid.initialize = function shieldedMermaidInit(config) {
                if (config && config.securityLevel === 'loose') {
                console.warn(
                        LOG,
                        'mermaid.initialize: securityLevel "loose" bloqueado → substituído por "antiscript".'
                    );
                    config = Object.assign({}, config, { securityLevel: 'antiscript' });
                }
                return originalInit(config);
            };

            global.mermaid.initialize._shielded = true;
            console.log(LOG, 'Patch Mermaid instalado (securityLevel: loose → antiscript).');
        }

        // Começa a tentar após o DOM estar pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', tentar);
        } else {
            tentar();
        }
    })();


    console.log(LOG, 'security.js v1.0 carregado — 3 shields ativos.');

})(window);
