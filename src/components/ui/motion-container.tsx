"use client";

import * as React from "react";
import { motion, type HTMLMotionProps } from "motion/react";

export interface MotionContainerProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
}

export function MotionContainer({ children, className, ...props }: MotionContainerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export { motion };
