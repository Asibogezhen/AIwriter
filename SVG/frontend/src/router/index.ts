import { createRouter, createWebHashHistory } from "vue-router";
import Home from "../views/Home.vue";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", name: "home", component: Home },
    { path: "/result/:id", name: "result", component: Home },
  ],
});

export default router;
