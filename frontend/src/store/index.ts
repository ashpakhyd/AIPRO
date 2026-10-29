import { configureStore } from '@reduxjs/toolkit'
import { newsApi } from './newsApi'

export const store = configureStore({
  reducer: {
    [newsApi.reducerPath]: newsApi.reducer,
  },
  middleware: (getDefault) => getDefault().concat(newsApi.middleware),
})

export type RootState = ReturnType<typeof store.getState>
