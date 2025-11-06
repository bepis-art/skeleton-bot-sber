/** Интерфейс для любого обьекта. */
export interface IObject<T = any> {     // eslint-disable-line @typescript-eslint/no-explicit-any
    [propName: string]: T
}
