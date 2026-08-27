interface SigilModuleErrors {
    cycle?: string | null;
    failed?: Set<string>;
    missing?: Set<string>;
    unloaded?: Set<string>;
}

interface SigilModuleFactory {
    deps: string[];
    fn: SigilModuleFactoryFn;
    ignoreMissingDeps: boolean;
}

class SigilModuleLoader {
    bus: EventTarget;
    checkErrorProm: Promise<void> | null;
    debug: boolean;
    /**
     * Mapping [name => factory]
     */
    factories: Map<string, SigilModuleFactory>;
    /**
     * Names of failed modules
     */
    failed: Set<string>;
    /**
     * Names of modules waiting to be started
     */
    jobs: Set<string>;
    /**
     * Mapping [name => module]
     */
    modules: Map<string, SigilModule>;

    constructor(root?: HTMLElement);

    addJob: (name: string) => void;

    define: (
        name: string,
        deps: string[],
        factory: SigilModuleFactoryFn,
        lazy?: boolean
    ) => SigilModule;

    findErrors: (jobs?: Iterable<string>) => SigilModuleErrors;

    findJob: () => string | null;

    reportErrors: (errors: SigilModuleErrors) => Promise<void>;

    sortFactories: () => void;

    startModule: (name: string) => SigilModule;

    startModules: () => void;
}

type SigilModule = Record<string, any>;

type SigilModuleFactoryFn = (require: (dependency: string) => SigilModule) => SigilModule;

declare const sigil: {
    csrf_token: string;
    debug: string;
    define: SigilModuleLoader["define"];
    loader: SigilModuleLoader;
};
