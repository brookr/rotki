import { type Ref } from 'vue';
import { useBalancesStore } from '@/store/balances';
import { useNotificationsStore } from '@/store/notifications';
import { useSessionAuthStore } from '@/store/session/auth';
import { usePeriodicStore } from '@/store/session/periodic';
import { useWatchersStore } from '@/store/session/watchers';
import { useFrontendSettingsStore } from '@/store/settings/frontend';
import { useTasks } from '@/store/tasks';
import { useWebsocketStore } from '@/store/websocket';
import { startPromise } from '@/utils';
import { logger } from '@/utils/logging';

const PERIODIC = 'periodic';
const TASK = 'task';
const WATCHER = 'watcher';
const BALANCES = 'balances';

export const useMonitorStore = defineStore('monitor', () => {
  const monitors: Ref<Record<string, any>> = ref({});

  const { logged } = storeToRefs(useSessionAuthStore());
  const { check } = usePeriodicStore();
  const { consume } = useNotificationsStore();
  const { fetchWatchers } = useWatchersStore();
  const { monitor } = useTasks();
  const { autoRefresh } = useBalancesStore();

  const { queryPeriod, refreshPeriod } = storeToRefs(
    useFrontendSettingsStore()
  );

  const ws = useWebsocketStore();
  const { connected } = storeToRefs(ws);
  const { connect, disconnect } = ws;

  const fetch = (): void => {
    if (get(logged)) {
      startPromise(check());
    }

    if (!get(connected)) {
      startPromise(consume());
    }
  };

  const connectWebSocket = async (restarting: boolean): Promise<void> => {
    try {
      await connect();
      const activeMonitors = get(monitors);
      if (!activeMonitors[PERIODIC]) {
        if (!restarting) {
          fetch();
        }

        activeMonitors[PERIODIC] = setInterval(fetch, get(queryPeriod) * 1000);
        set(monitors, activeMonitors);
      }
    } catch (e: any) {
      logger.error(e);
    }
  };

  const startTaskMonitoring = (restarting: boolean): void => {
    const activeMonitors = get(monitors);

    if (!activeMonitors[TASK]) {
      if (!restarting) {
        startPromise(monitor());
      }
      activeMonitors[TASK] = setInterval(() => startPromise(monitor()), 2000);
      set(monitors, activeMonitors);
    }
  };

  const startWatcherMonitoring = (restarting: boolean): void => {
    const activeMonitors = get(monitors);
    if (!activeMonitors[WATCHER]) {
      if (!restarting) {
        startPromise(fetchWatchers());
      }
      // check for watchers every 6 minutes (approx. half the firing time
      // of the server-side watchers)
      activeMonitors[WATCHER] = setInterval(
        () => startPromise(fetchWatchers()),
        360000
      );
      set(monitors, activeMonitors);
    }
  };

  const startBalanceRefresh = (): void => {
    const period = get(refreshPeriod) * 60 * 1000;
    const activeMonitors = get(monitors);
    if (!activeMonitors[BALANCES] && period > 0) {
      activeMonitors[BALANCES] = setInterval(autoRefresh, period);
      set(monitors, activeMonitors);
    }
  };

  /**
   * This function is called periodically, queries some data from the
   * client and updates the UI with the response.
   */
  const start = function (restarting = false): void {
    startPromise(connectWebSocket(restarting));
    startTaskMonitoring(restarting);
    startWatcherMonitoring(restarting);
    startBalanceRefresh();
  };

  const stop = (): void => {
    disconnect();
    const activeMonitors = get(monitors);
    for (const key in activeMonitors) {
      clearInterval(activeMonitors[key]);
      delete activeMonitors[key];
    }
    set(monitors, activeMonitors);
  };

  const restart = (): void => {
    stop();
    start(true);
  };

  return {
    start,
    stop,
    restart
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useMonitorStore, import.meta.hot));
}
