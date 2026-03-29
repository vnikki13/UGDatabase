import { createFormHookContexts, createFormHook } from '@tanstack/react-form';
import { TextField } from '../components/FormFields/TextField';

// Export contexts and a utility hook for child components
export const { fieldContext, formContext, useFieldContext } = createFormHookContexts();

// Create a custom form hook (optional but useful for pre-binding UI components)
export const { useAppForm } = createFormHook({
  fieldContext,
  formContext,
  fieldComponents: {
    TextField
  }, // Add pre-bound field components here
  formComponents: {},
});

