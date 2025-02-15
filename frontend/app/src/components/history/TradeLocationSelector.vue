<script setup lang="ts">
import { type PropType } from 'vue';
import LocationIcon from '@/components/history/LocationIcon.vue';
import { type TradeLocation } from '@/types/history/trade-location';
import { type TradeLocationData, useTradeLocations } from '@/types/trades';

const { t } = useI18n();

const props = defineProps({
  value: { required: true, type: Object as PropType<TradeLocation> },
  availableLocations: {
    required: false,
    type: Array as PropType<string[]>,
    default: () => []
  },
  outlined: { required: false, type: Boolean, default: false }
});

const emit = defineEmits(['input']);
const { availableLocations, value } = toRefs(props);
const { tradeLocations } = useTradeLocations();

const locations = computed<TradeLocationData[]>(() => {
  return get(tradeLocations).filter(location =>
    get(availableLocations).includes(location.identifier)
  );
});

const name = computed<string>(() => {
  return (
    get(tradeLocations).find(location => location.identifier === get(value))
      ?.name ?? ''
  );
});

const input = (value: TradeLocation) => {
  emit('input', value);
};
</script>

<template>
  <v-row>
    <v-col cols="12">
      <v-card :flat="outlined">
        <div class="mx-4 py-2" :class="outlined ? 'px-3' : null">
          <v-autocomplete
            :value="value"
            :items="locations"
            hide-details
            hide-selected
            hide-no-data
            clearable
            chips
            :class="outlined ? 'trade-location-selector--outlined' : null"
            :outlined="outlined"
            :label="t('trade_location_selector.label')"
            item-text="name"
            item-value="identifier"
            @input="input"
          >
            <template #selection="{ item }">
              <location-icon horizontal :item="item" />
            </template>
            <template #item="{ item }">
              <location-icon horizontal :item="item" />
            </template>
          </v-autocomplete>
        </div>
        <v-card-text>
          {{
            !value
              ? t('trade_location_selector.selection_none')
              : t('trade_location_selector.selection_single', {
                  location: name
                })
          }}
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<style scoped lang="scss">
.trade-location-selector {
  &--outlined {
    :deep() {
      /* stylelint-disable */
      .v-label:not(.v-label--active) {
        /* stylelint-enable */
        top: 24px;
      }

      .v-input {
        &__icon {
          &--clear {
            margin-top: 6px;
          }

          &--append {
            margin-top: 6px;
          }
        }
      }
    }
  }
}
</style>
