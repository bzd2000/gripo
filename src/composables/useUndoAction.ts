import { Notify } from 'quasar';

export function useUndoAction() {
  function perform(opts: {
    message: string;
    action: () => Promise<void>;
    undo: () => Promise<void>;
    timeout?: number;
  }) {
    void opts.action();
    Notify.create({
      message: opts.message,
      color: 'dark',
      position: 'bottom',
      timeout: opts.timeout ?? 5000,
      actions: [
        {
          label: 'Undo',
          color: 'yellow',
          handler: () => {
            void opts.undo();
          },
        },
      ],
    });
  }

  return { perform };
}
