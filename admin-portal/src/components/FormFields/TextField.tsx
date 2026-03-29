import { useFieldContext } from "../../hooks/questionForm"
import { FormControl, TextField as Text } from "@mui/material"


export function TextField({ label, isRequired = true }: { label: string, isRequired?: boolean }) {
    const field = useFieldContext<string>()
    return (
        <FormControl sx={{ m: 1, width: 300 }}>
            <Text
                label={label}
                variant="outlined"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                multiline
                required={isRequired}
            />
        </FormControl>
    )
}